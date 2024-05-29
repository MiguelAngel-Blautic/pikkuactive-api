from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_series, tbl_ejercicios, tbl_entrenamientos

router = APIRouter()


@router.get("/", response_model=List[schemas.Ejercicio])
def read_ejercicios_by_serie(
    serie_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    if current_user.fkRol == 2:
        serie = db.query(tbl_series).get(serie_id)
        if not serie:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if not plan:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == serie_id).all()
    else:
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkCreador == current_user.id).filter(tbl_ejercicios.fkSerie == serie_id).all()
    return ejercicios


@router.get("/{id}", response_model=schemas.Ejercicio)
def read_ejercicios_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    ejercicio = db.query(tbl_ejercicios).filter(tbl_ejercicios.id == id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="The exercise doesn't exist")
    if current_user.fkRol == 2:
        serie = db.query(tbl_series).get(ejercicio.fkSerie)
        if not serie:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return ejercicio


@router.post("/", response_model=schemas.Ejercicio)
def create_ejercicio(
    *,
    db: Session = Depends(deps.get_db),
    ejercicio_in: schemas.EjercicioCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    ejercicios = read_ejercicios_by_serie(db=db, current_user=current_user, serie_id=ejercicio_in.fkSerie)
    newEjercicio = tbl_ejercicios(fkCreador=current_user.id,
                        fkSerie=ejercicio_in.fkSerie,
                        fldNDescanso=ejercicio_in.fldNDescanso,
                        fldNOrden=len(ejercicios)+1,
                        fldNRepeticiones=ejercicio_in.fldNRepeticiones,
                        fldNDuracion=ejercicio_in.fldNDuracion,
                        fldFVelocidad=ejercicio_in.fldFVelocidad,
                        fldFUmbral=ejercicio_in.fldFUmbral,
                        fkModelo=ejercicio_in.fkModelo,
                        fldSToken=ejercicio_in.fldSToken)
    db.add(newEjercicio)
    db.commit()
    db.refresh(newEjercicio)
    return newEjercicio


@router.put("/{id}", response_model=schemas.Ejercicio)
def update_serie(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    ejercicio_in: schemas.EjercicioUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    ejercicio = read_ejercicios_by_id(id=id, db=db, current_user=current_user)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="The exercise doesn't exist")
    ejercicio.fldNDescanso = ejercicio_in.fldNDescanso
    ejercicio.fldNRepeticiones = ejercicio_in.fldNRepeticiones
    ejercicio.fldNDuracion = ejercicio_in.fldNDuracion
    ejercicio.fldFVelocidad = ejercicio_in.fldFVelocidad
    ejercicio.fldFUmbral = ejercicio_in.fldFUmbral
    ejercicio.fkModelo = ejercicio_in.fkModelo
    ejercicio.fldSToken = ejercicio_in.fldSToken
    db.commit()
    db.refresh(ejercicio)
    return ejercicio


@router.delete("/{id}")
def delete_ejericio(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    ejercicio = read_ejercicios_by_id(id=id, db=db, current_user=current_user)
    change_order(ejercicio.id, 0, current_user=current_user, db=db)
    db.delete(ejercicio)
    db.commit()
    return


@router.post("/orden", response_model=schemas.Ejercicio)
def change_order(
    ejercicio_id: int,
    new_posicion: int = 0,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Cambia la posicion de una serie
    """
    ejercicio = read_ejercicios_by_id(id=ejercicio_id, db=db, current_user=current_user)
    if new_posicion == 0:
        total_ejercicios = read_ejercicios_by_serie(serie_id=ejercicio.fkSerie, db=db, current_user=current_user)
        new_posicion = len(total_ejercicios) + 1
    if(new_posicion > ejercicio.fldNOrden):
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == ejercicio.fkSerie).filter(tbl_ejercicios.fldNOrden > ejercicio.fldNOrden).filter(tbl_ejercicios.fldNOrden <= new_posicion).all()
        for e in ejercicios:
            e.fldNOrden = e.fldNOrden - 1
        ejercicio.fldNOrden = new_posicion
    else:
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == ejercicio.fkSerie).filter(
            tbl_ejercicios.fldNOrden < ejercicio.fldNOrden).filter(tbl_ejercicios.fldNOrden >= new_posicion).all()
        for e in ejercicios:
            e.fldNOrden = e.fldNOrden + 1
        ejercicio.fldNOrden = new_posicion
    db.commit()
    db.refresh(ejercicio)
    return ejercicio

def clonar(
    old_serie: int,
    new_serie: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == old_serie).all()
    for e in ejercicios:
        new = tbl_ejercicios(fkSerie=new_serie,
                            fldNDescanso=e.fldNDescanso,
                            fldNDuracion=e.fldNDuracion,
                            fldNRepeticiones=e.fldNRepeticiones,
                            fldFVelocidad=e.fldFVelocidad,
                            fldFUmbral=e.fldFUmbral,
                            fldNOrden=e.fldNOrden,
                            fkModelo=e.fkModelo,
                            fkCreador=e.fkCreador,
                            fldSToken=e.fldSToken)
        db.add(new)
        db.commit()
        db.refresh(new)
    return




























