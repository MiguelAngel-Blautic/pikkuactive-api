from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.models import read_models, read_model
from app.models import tbl_model

router = APIRouter()


@router.get("/", response_model=List[schemas.Movement])
def read_movements(
        id_model: Optional[int] = None,
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve movements.
    """
    if id_model is None:
        models_user = read_models(db=db, current_user=current_user)
        movements = crud.movement.get_all_by_owner(db=db, models=models_user, skip=skip, limit=limit)
    else:
        model = read_model(db=db, id=id_model, current_user=current_user)
        models_user: List[tbl_model] = [model]
        movements = crud.movement.get_all_by_owner(
            db=db, models=models_user, skip=skip, limit=limit
        )
    return movements


@router.post("/", response_model=schemas.Movement)
def create_movement(
        *,
        id_model: int,
        db: Session = Depends(deps.get_db),
        movement_in: schemas.MovementCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new movement.
    """
    model = read_model(db=db, id=id_model, current_user=current_user)
    movement = crud.movement.create_with_owner(db=db, obj_in=movement_in, fkOwner=model.id)
    return movement


@router.put("/{id}", response_model=schemas.Movement)
def update_movement(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        movement_in: schemas.MovementUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an movement.
    """
    movement = read_movement(db=db, id=id, current_user=current_user)
    movement = crud.model.update(db=db, db_obj=movement, obj_in=movement_in)
    return movement


@router.get("/{id}", response_model=schemas.Movement)
def read_movement(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get movement by ID.
    """
    movement = crud.movement.get(db=db, id=id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    # Check owner is current_user
    read_model(db=db, id=movement.fkOwner, current_user=current_user)
    return movement


@router.delete("/{id}", response_model=schemas.Movement)
def delete_movement(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an movement.
    """
    read_movement(db=db, id=id, current_user=current_user)
    movement = crud.movement.remove(db=db, id=id)
    return movement
