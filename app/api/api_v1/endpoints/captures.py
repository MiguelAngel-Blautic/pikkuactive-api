from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.models import read_models, read_model

router = APIRouter()

@router.post("/", response_model=schemas.Capture)
def create_capture(
        *,
        id_movement: int,
        db: Session = Depends(deps.get_db),
        capture_in: schemas.CaptureCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new capture.
    """
    movement = crud.movement.get(db=db, id=id_movement)
    # comprobar tamaño de la los datos segun el tiempo y el numero de dispositivos 
    # size_data = movement
    # if movementlen(capture_in.data)

    capture = crud.capture.create_with_owner(db=db, obj_in=capture_in, movement=movement)
    #capture.ecg = []
    #capture.mpu = []
    return capture
