from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_movement, tbl_model, tbl_dispositivo_sensor
from app.models.tbl_model import TrainingStatus
from app.models.tbl_position import tbl_position
from app.schemas import MovementCreate

router = APIRouter()


@router.get("/", response_model=List[schemas.DeviceSensor])
def read_devices(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve positions.
    """
    devices = db.query(tbl_dispositivo_sensor).filter(tbl_dispositivo_sensor.fkOwner == id).all()
    db.close()
    return devices


@router.post("/", response_model=schemas.DeviceSensor)
def enable_device(
    id: int,
    enable: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve positions.
    """
    device = db.query(tbl_dispositivo_sensor).get(id)
    if device is not None:
        device.fldBActive = max(0, min(1, enable))
        db.commit()
        db.refresh(device)
    return device