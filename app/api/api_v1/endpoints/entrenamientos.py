from datetime import date
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import planes, bloques
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_entrenamientos

router = APIRouter()


@router.get("/", response_model=List[schemas.Entrenamiento])
def read_entrenamientos(
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkCreador == current_user.id).filter(tbl_entrenamientos.fkPlan == None).all()
    return entrenamientos


@router.get("/dia", response_model=List[schemas.Entrenamiento])
def read_entrenamientos_by_dia(
    dia: date,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    if current_user.fkRol == 1:
        entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fldDDia == dia).filter(
            tbl_entrenamientos.fkCreador == current_user.id).all()
        return entrenamientos
    else:
        planes = db.query(tbl_planes).filter(tbl_planes.fkCliente == current_user.id).all()
        entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fldDDia == dia).filter(
            tbl_entrenamientos.fkPlan.in_([p.id for p in planes])).all()
        return entrenamientos


@router.get("/plan", response_model=List[schemas.Entrenamiento])
def read_entrenamientos_by_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkCreador == current_user.id).filter(tbl_entrenamientos.fkPlan == plan_id).filter(tbl_entrenamientos.fldDDia == None).all()
    return entrenamientos


@router.get("/{id}", response_model=schemas.Entrenamiento)
def read_entrenamiento_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    entrenamiento = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkCreador == current_user.id).filter(tbl_entrenamientos.id == id).first()
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The id doesn't exist")
    if current_user.fkRol == 2:
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return entrenamiento



@router.post("/", response_model=schemas.Entrenamiento)
def create_entrenamiento(
    *,
    db: Session = Depends(deps.get_db),
    entrenamiento_in: schemas.EntrenamientoCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    newEntrenamiento = tbl_entrenamientos(fldSNombre=entrenamiento_in.fldSNombre,
                        fkCreador=current_user.id)
    db.add(newEntrenamiento)
    db.commit()
    db.refresh(newEntrenamiento)
    return newEntrenamiento


@router.post("/plan", response_model=schemas.Entrenamiento)
def asignar_entrenamiento_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    entrenamiento_id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Asignar un entrenamiento generico a un plan
    """
    plan = planes.read_planes_by_id(db=db, current_user=current_user, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=entrenamiento_id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    newEntrenamiento = tbl_entrenamientos(fldSNombre=entrenamiento.fldSNombre,
                                          fkCreador=current_user.id,
                                          fkPadre=entrenamiento.id,
                                          fkPlan=plan.id)
    db.add(newEntrenamiento)
    db.commit()
    db.refresh(newEntrenamiento)
    bloques.clonar(old_entrenamiento=entrenamiento.id, new_entrenamiento=newEntrenamiento.id, db=db)
    return newEntrenamiento


@router.post("/sesion", response_model=schemas.Entrenamiento)
def asignar_entrenamiento_sesion(
    *,
    db: Session = Depends(deps.get_db),
    dia: date,
    entrenamiento_id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Asignar un entrenamiento de un plan a una fecha
    """
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=entrenamiento_id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    plan = planes.read_planes_by_id(db=db, current_user=current_user, id=entrenamiento.fkPlan)
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    entrenamientoAct = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkPlan == plan.id).filter(
        tbl_entrenamientos.fldDDia == dia).all()
    if len(entrenamientoAct) > 0:
        raise HTTPException(status_code=404, detail="The training already exist")
    newEntrenamiento = tbl_entrenamientos(fldSNombre=entrenamiento.fldSNombre,
                                          fkCreador=current_user.id,
                                          fkPadre=entrenamiento.id,
                                          fkPlan=plan.id,
                                          fldDDia=dia)
    db.add(newEntrenamiento)
    db.commit()
    db.refresh(newEntrenamiento)
    bloques.clonar(old_entrenamiento=entrenamiento.id, new_entrenamiento=newEntrenamiento.id, db=db)
    return newEntrenamiento


@router.put("/{id}", response_model=schemas.Plan)
def update_entrenamiento(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    entrenamiento_in: schemas.EntrenamientoUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    entrenamiento.fldSNombre = entrenamiento_in.fldSNombre
    entrenamiento.fldDDia = entrenamiento_in.fldDDia
    db.commit()
    db.refresh(entrenamiento)
    return entrenamiento


@router.delete("/{id}")
def delete_entrenamiento(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    db.delete(entrenamiento)
    db.commit()
    return
