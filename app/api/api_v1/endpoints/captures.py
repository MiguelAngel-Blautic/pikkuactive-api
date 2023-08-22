from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.models import read_models, read_model
from app.models import tbl_movement

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


@router.delete("/")
def delete_capture(
        *,
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete capture.
    """
    capture = crud.capture.get(db=db, id=id)
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    db.delete(capture)
    db.commit()
    return


@router.get("/", response_model=schemas.Capture)
def read_capture(
        *,
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new capture.
    """
    capture = crud.capture.get(db=db, id=id)
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    return capture


@router.post("/change/", response_model=schemas.Capture)
def change_capture(
        *,
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new capture.
    """
    capture = crud.capture.get(db=db, id=id)
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    movement = crud.movement.get(db=db, id=capture.fkOwner)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    movement2 = db.query(tbl_movement).filter(tbl_movement.fkOwner == movement.fkOwner).filter(tbl_movement.id != movement.id).first()
    if not movement2:
        raise HTTPException(status_code=404, detail="Movement 2 not found")
    capture.fkOwner = movement2.id
    db.commit()
    db.refresh(capture)
    return capture

