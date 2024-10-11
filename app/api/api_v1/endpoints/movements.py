from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_movement, tbl_model
from app.models.tbl_model import TrainingStatus
from app.models.tbl_position import tbl_position
from app.schemas import MovementCreate

router = APIRouter()


@router.get("/", response_model=List[schemas.Movement])
def read_movements(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve positions.
    """
    movements = db.query(tbl_movement).filter(tbl_movement.fkOwner == id).all()
    db.close()
    return movements


@router.post("/", response_model=schemas.Movement)
def create_movement(
    id: int,
    nombre: str,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve positions.
    """
    movement_incorrect = MovementCreate(fldSLabel=nombre, fldSDescription=nombre)
    mov = crud.movement.create_with_owner(db=db, obj_in=movement_incorrect, fkOwner=id)
    model = db.query(tbl_model).get(id)
    model.fldSStatus = TrainingStatus.no_training_pending
    db.commit()
    return mov