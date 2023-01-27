from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_sesion, tbl_model
from app.models.tbl_ejercicio import tbl_ejercicio
from app.schemas import SesionCreate, EjercicioCreate, Umbral, EjercicioResumen

router = APIRouter()


@router.get("/", response_model=List[schemas.Sesion])
def read_sesiones(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    rol = current_user.fkRol
    plan: List[tbl_sesion] = crud.sesion.get_multi_by_rol(db, user=current_user.id, rol=rol, skip=skip, limit=limit)
    return plan


@router.post("/", response_model=schemas.Sesion)
def create_plan(
        *,
        db: Session = Depends(deps.get_db),
        plan_in: schemas.SesionCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new model.
    """
    if not plan_in.fkCreador:
        plan_in.fkCreador = current_user.id
    if current_user.fkRol > 1:
        plan = crud.sesion.create_with_owner(db=db, obj_in=plan_in)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return plan


@router.put("/{id}", response_model=schemas.Sesion)
def update_plan(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        plan_in: schemas.SesionUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an model.
    """
    plan = read_plan(db=db, id=id, current_user=current_user)  # Check model exists
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        plan = crud.sesion.update(db=db, db_obj=plan, obj_in=plan_in)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return plan


@router.get("/{id}", response_model=schemas.Sesion)
def read_plan(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    # plan = crud.sesion.get(db=db, id=id)
    plan = crud.sesion.getCompleta(db=db, id=id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    # if not check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
    #    raise HTTPException(status_code=400, detail="Not enough permissions")
    return plan


@router.delete("/{id}", response_model=schemas.Sesion)
def delete_plan(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an model.
    """
    read_plan(db=db, id=id, current_user=current_user)  # Check model exists
    plan = crud.sesion.get(db=db, id=id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        model = crud.sesion.remove(db=db, id=id)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return model


def check_permission(
        *,
        db: Session,
        user: int,
        plan: tbl_sesion,
        rol: int,
) -> Any:
    if rol == 1:
        res = crud.asignado.count(db=db, user=user, plan=plan.id) > 1
    else:
        if rol == 2:
            res = (user == plan.fkCreador)
        else:
            if rol == 3:
                res = crud.asignado.count(db=db, user=user, plan=plan.id) > 1
                res = res or (user == plan.fkCreador)
            else:
                res = True

    return res
