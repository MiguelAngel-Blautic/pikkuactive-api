from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_sesion
from app.models.tbl_ejercicio import tbl_ejercicio
from app.api.api_v1.endpoints.plan import read_plan, check_permission

router = APIRouter()


@router.get("/", response_model=List[schemas.Ejercicio])
def read_ejercicios(
        db: Session = Depends(deps.get_db),
        plan_id: int = 0,
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    rol = current_user.fkRol
    plan = read_plan(db=db, id=plan_id, current_user=current_user)  # Check model exists
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    ejercicio: List[tbl_ejercicio] = crud.ejercicio.get_multi_by_rol(db=db, user=current_user.id, rol=rol, skip=skip, limit=limit, id=plan_id)
    return ejercicio


@router.post("/", response_model=schemas.Ejercicio)
def create_ejercicio(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        ejercicio_in: schemas.EjercicioCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    plan = read_plan(db=db, id=id, current_user=current_user)  # Check model exists
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol) and current_user.fkRol > 1:
        ejercicio = crud.ejercicio.create_with_owner(db=db, db_obj=plan, obj_in=ejercicio_in)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return ejercicio


@router.put("/repeticiones", response_model=int)
def update_Repeticiones(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        repeticiones: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    return crud.ejercicio.repeticiones(db=db, id=id, valor=repeticiones)


@router.put("/umbral", response_model=int)
def update_Umbral(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        umbral: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    return crud.ejercicio.umbral(db=db, id=id, valor=umbral)


@router.put("/{id}", response_model=schemas.Ejercicio)
def update_Ejercicio(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        ejercicio_in: schemas.EjercicioUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an model.
    """
    ejercicio = read_ejercicio(db=db, id=id, current_user=current_user)  # Check model exists
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio not found")
    plan = read_plan(db=db, id=ejercicio.fkPlan, current_user=current_user)  # Check model exists
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        ejercicio = crud.ejercicio.update(db=db, db_obj=ejercicio, obj_in=ejercicio_in)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return ejercicio


@router.get("/usuario", response_model=List[schemas.EjercicioResumen])
def readEjercicios(
        *,
        db: Session = Depends(deps.get_db),
        id: Optional[int] = None,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    if id:
        usuario = id
    else:
        usuario = current_user.id
    ejercicios = crud.ejercicio.readUser(db=db, user=usuario)
    return ejercicios


@router.get("/{id}", response_model=schemas.Ejercicio)
def read_ejercicio(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    ejercicio = crud.ejercicio.get(db=db, id=id)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio not found")
    plan = read_plan(db=db, id=ejercicio.fkPlan, current_user=current_user)  # Check model exists
    if not check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return ejercicio


@router.delete("/{id}", response_model=schemas.Ejercicio)
def delete_ejercicio(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an model.
    """
    read_ejercicio(db=db, id=id, current_user=current_user)  # Check model exists
    ejercicio = crud.ejercicio.get(db=db, id=id)
    plan = read_plan(db=db, id=ejercicio.fkPlan, current_user=current_user)  # Check model exists
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Plan not found")
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        ejercicio = crud.ejercicio.remove(db=db, id=id)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return ejercicio