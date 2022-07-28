from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.tbl_position import tbl_position

router = APIRouter()


@router.get("/", response_model=List[schemas.Position])
def read_positions(
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve positions.
    """
    positions = crud.position.get_multi(db=db)
    return positions


@router.post("/", response_model=schemas.Position)
def create_position(
    *,
    db: Session = Depends(deps.get_db),
    model_in: schemas.PositionCreate,
    current_user: models.tbl_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new position.
    """
    position = crud.position.create(db=db, obj_in=model_in)
    return position


@router.put("/{id}", response_model=schemas.Position)
def update_position(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    position_in: schemas.PositionUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update an position.
    """
    position = read_position(db=db, id=id, current_user=current_user)  # check position exist
    position = crud.position.update(db=db, db_obj=position, obj_in=position_in)
    return position


@router.get("/{id}", response_model=schemas.Position)
def read_position(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    position = crud.position.get(db=db, id=id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.delete("/{id}", response_model=schemas.Position)
def delete_position(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete an position.
    """
    read_position(db=db, id=id, current_user=current_user)  # check position exist
    position = crud.position.remove(db=db, id=id)
    return position
