from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.ejercicio import read_ejercicio
from app.models import tbl_sesion
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales
from app.models.tbl_sesion import tbl_planes
from app.api.api_v1.endpoints.plan import read_plan, check_permission

router = APIRouter()


@router.get("/", response_model=List[schemas.Umbral])
def read_umbrales(
        db: Session = Depends(deps.get_db),
        ejercicio: int = 0,
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    ejercicio = read_ejercicio(db=db, id=ejercicio, current_user=current_user)
    umbral: List[tbl_umbrales] = crud.umbral.get_multi_valores(db=db, ejercicio=ejercicio.id, skip=skip, limit=limit)
    return umbral


@router.post("/", response_model=schemas.Umbral)
def create_umbral(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        umbral_in: schemas.UmbralCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    ejercicio = read_ejercicio(db=db, id=id, current_user=current_user)  # Check model exists
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio not found")
    ejercicio = crud.umbral.create_with_owner(db=db, db_obj=ejercicio, obj_in=umbral_in)
    return ejercicio


@router.put("/{id}", response_model=schemas.Umbral)
def update_umbral(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        umbral_in: schemas.UmbralUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an model.
    """
    umbral = read_umbral(db=db, id=id, current_user=current_user)  # Check model exists
    if not umbral:
        raise HTTPException(status_code=404, detail="Umbral not found")
    umbral = crud.umbral.update(db=db, db_obj=umbral, obj_in=umbral_in)
    return umbral


@router.get("/{id}", response_model=schemas.Umbral)
def read_umbral(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    umbral = crud.umbral.get(db=db, id=id)
    if not umbral:
        raise HTTPException(status_code=404, detail="Umbral not found")
    ejercicio = read_ejercicio(db=db, id=umbral.fkEjercicio, current_user=current_user)
    if not ejercicio:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return umbral


@router.delete("/{id}", response_model=schemas.Umbral)
def delete_umbral(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an model.
    """
    read_umbral(db=db, id=id, current_user=current_user)  # Check model exists
    umbral = crud.umbral.get(db=db, id=id)
    if not umbral:
        raise HTTPException(status_code=404, detail="Umbral not found")
    umbral = crud.umbral.remove(db=db, id=id)
    return umbral
