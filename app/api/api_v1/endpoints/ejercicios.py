from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import resultados
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_series, tbl_ejercicios, tbl_entrenamientos
from app.models.tbl_resultados import tbl_registro_ejercicios, tbl_resultados
from app.schemas import RegistroEjercicioDB, EjercicioTipos
from app.schemas.ejercicio import Resultado

router = APIRouter()


@router.get("/", response_model=List[EjercicioTipos])
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
    tipodatos = []
    res = []
    for e in ejercicios:
        tipos = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == e.id).all()
        for t in tipos:
            tipodatos.append(RegistroEjercicioDB(fkEjercicio=t.fkEjercicio, id=t.id, fkTipoDato=t.fkTipoDato))
        res.append(EjercicioTipos(
            tipodatos=tipodatos,
            fkSerie=e.fkSerie,
            fldNOrden=e.fldNOrden,
            fldNDescanso=e.fldNDescanso,
            fldNRepeticiones=e.fldNRepeticiones,
            fldNDuracion=e.fldNDuracion,
            fldNDuracionEfectiva=e.fldNDuracionEfectiva,
            fldFVelocidad=e.fldFVelocidad,
            fldFUmbral=e.fldFUmbral,
            fkModelo=e.fkModelo,
            fldSToken=e.fldSToken,
            id=e.id
        ))
        tipodatos = []
    return res


def read_ejercicios_by_idDB(
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


@router.get("/{id}", response_model=schemas.EjercicioTipos)
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
    tipodatos = []
    tipos = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == ejercicio.id).all()
    for t in tipos:
        tipodatos.append(RegistroEjercicioDB(fkEjercicio=t.fkEjercicio, id=t.id, fkTipoDato=t.fkTipoDato))
    res = EjercicioTipos(
        tipodatos=tipodatos,
        fkSerie=ejercicio.fkSerie,
        fldNOrden=ejercicio.fldNOrden,
        fldNDescanso=ejercicio.fldNDescanso,
        fldNRepeticiones=ejercicio.fldNRepeticiones,
        fldNDuracion=ejercicio.fldNDuracion,
        fldNDuracionEfectiva=ejercicio.fldNDuracionEfectiva,
        fldFVelocidad=ejercicio.fldFVelocidad,
        fldFUmbral=ejercicio.fldFUmbral,
        fkModelo=ejercicio.fkModelo,
        fldSToken=ejercicio.fldSToken,
        id=ejercicio.id
    )
    return res

def read_valores_ejercicios(
    *,
    db: Session = Depends(deps.get_db),
    serie: int
) -> List[Resultado]:
    ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == serie).all()
    res = []
    for e in ejercicios:
        if e.fldNRepeticiones is not None:
            dato = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == e.id).filter(tbl_registro_ejercicios.fkTipoDato == 2).first()
            datos = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == dato.id).all()
            adherencia = (len(datos)*100) / e.fldNRepeticiones
            res.append(Resultado(id=e.id, adherencia=adherencia, completo=100, nombre=""))
        # res.append(Resultado(id=e.id, nombre=e.fld))
    return res


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
                        fldNDuracionEfectiva=ejercicio_in.fldNDuracionEfectiva,
                        fldFVelocidad=ejercicio_in.fldFVelocidad,
                        fldFUmbral=ejercicio_in.fldFUmbral,
                        fkModelo=ejercicio_in.fkModelo,
                        fldSToken=ejercicio_in.fldSToken)
    db.add(newEjercicio)
    db.commit()
    db.refresh(newEjercicio)
    new = tbl_registro_ejercicios(fkTipoDato=0,
                                  fkEjercicio=newEjercicio.id)
    db.add(new)
    db.commit()
    for r in ejercicio_in.registros:
        new = tbl_registro_ejercicios(fkTipoDato=r,
                                      fkEjercicio=newEjercicio.id)
        db.add(new)
        db.commit()
    return newEjercicio


@router.put("/{id}", response_model=schemas.Ejercicio)
def update_ejercicio(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    ejercicio_in: schemas.EjercicioUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    ejercicio = read_ejercicios_by_idDB(id=id, db=db, current_user=current_user)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="The exercise doesn't exist")
    ejercicio.fldNDescanso = ejercicio_in.fldNDescanso
    ejercicio.fldNRepeticiones = ejercicio_in.fldNRepeticiones
    ejercicio.fldNDuracion = ejercicio_in.fldNDuracion
    ejercicio.fldNDuracionEfectiva=ejercicio_in.fldNDuracionEfectiva
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
    ejercicio = read_ejercicios_by_idDB(id=id, db=db, current_user=current_user)
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
    ejercicio = read_ejercicios_by_idDB(id=ejercicio_id, db=db, current_user=current_user)
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
                            fldNDuracionEfectiva = e.fldNDuracionEfectiva,
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
        resultados.clonar(old_ejercicio=e.id, new_ejercicio=new.id, db=db)
    return




























