from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import entrenamientos, ejercicios
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_series, tbl_entrenamientos

router = APIRouter()


@router.get("/", response_model=List[schemas.Serie])
def read_series_by_bloque(
    bloque_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    if current_user.fkRol == 2:
        bloque = db.query(tbl_bloques).get(bloque_id)
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
    series = db.query(tbl_series).filter(tbl_series.fkCreador == current_user.id).filter(tbl_series.fkBloque == bloque_id).all()
    return series


@router.get("/{id}", response_model=schemas.Serie)
def read_series_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    serie = db.query(tbl_series).filter(tbl_series.fkCreador == current_user.id).filter(tbl_series.id == id).first()
    if not serie:
        raise HTTPException(status_code=404, detail="The serie doesn't exist")
    if current_user.fkRol == 2:
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return serie


@router.post("/", response_model=schemas.Serie)
def create_serie(
    *,
    db: Session = Depends(deps.get_db),
    serie_in: schemas.SerieCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    series = read_series_by_bloque(db=db, current_user=current_user, bloque_id=serie_in.fkBloque)
    newSerie = tbl_series(fldSDescripcion=serie_in.fldSDescripcion,
                        fkCreador=current_user.id,
                        fkBloque=serie_in.fkBloque,
                        fldNDescanso=serie_in.fldNDescanso,
                        fldNOrden=len(series)+1,
                        fldNRepeticiones=serie_in.fldNRepeticiones)
    db.add(newSerie)
    db.commit()
    db.refresh(newSerie)
    return newSerie


@router.put("/{id}", response_model=schemas.Serie)
def update_serie(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    serie_in: schemas.SerieUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    serie = read_series_by_id(id=id, db=db, current_user=current_user)
    if not serie:
        raise HTTPException(status_code=404, detail="The block doesn't exist")
    serie.fldSDescripcion = serie_in.fldSDescripcion
    serie.fldNDescanso = serie_in.fldNDescanso
    serie.fldNRepeticiones = serie_in.fldNRepeticiones
    db.commit()
    db.refresh(serie)
    return serie


@router.delete("/{id}")
def delete_serie(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    serie = read_series_by_id(id=id, db=db, current_user=current_user)
    change_order(serie.id, 0, current_user=current_user, db=db)
    db.delete(serie)
    db.commit()
    return


@router.post("/orden", response_model=schemas.Serie)
def change_order(
    serie_id: int,
    new_posicion: int = 0,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Cambia la posicion de una serie
    """
    serie = read_series_by_id(id=serie_id, db=db, current_user=current_user)
    if new_posicion == 0:
        total_series = read_series_by_bloque(bloque_id=serie.fkBloque, db=db, current_user=current_user)
        new_posicion = len(total_series) + 1
    if(new_posicion > serie.fldNOrden):
        series = db.query(tbl_series).filter(tbl_series.fkBloque == serie.fkBloque).filter(tbl_series.fldNOrden > serie.fldNOrden).filter(tbl_series.fldNOrden <= new_posicion).all()
        for s in series:
            s.fldNOrden = s.fldNOrden - 1
        serie.fldNOrden = new_posicion
    else:
        series = db.query(tbl_series).filter(tbl_series.fkBloque == serie.fkBloque).filter(
            tbl_series.fldNOrden < serie.fldNOrden).filter(tbl_series.fldNOrden >= new_posicion).all()
        for s in series:
            s.fldNOrden = s.fldNOrden + 1
        serie.fldNOrden = new_posicion
    db.commit()
    db.refresh(serie)
    return serie


def clonar(
    old_bloque: int,
    new_bloque: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    series = db.query(tbl_series).filter(tbl_series.fkBloque == old_bloque).all()
    for obj in series:
        new = tbl_series(fldSDescripcion=obj.fldSDescripcion,
                        fkBloque=new_bloque,
                        fldNRepeticiones=obj.id,
                        fldNDescanso=obj.id,
                        fldNOrden=obj.id,
                        fkCreador=obj.id)
        db.add(new)
        db.commit()
        db.refresh(new)
        ejercicios.clonar(old_serie=obj.id, new_serie=new.id)
    return


























