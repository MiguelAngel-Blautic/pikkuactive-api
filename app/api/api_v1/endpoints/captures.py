from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.models import read_models, read_model
from app.models import tbl_movement
from app.schemas import Capture
from app.schemas.data import Data

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
    # capture.ecg = []
    # capture.mpu = []

    model = crud.model.setPending(db=db, model=movement.fkOwner)
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
    res = []
    for d in capture.datos:
        res.append(Data(fkCaptura=d.fkCaptura,
                        fkDispositivoSensor=d.fkDispositivoSensor,
                        idPosicion=d.dispositivoSensor.sensor.id,
                        fldNSample=d.fldNSample,
                        fldFValor=d.fldFValor,
                        fldFValor2=d.fldFValor2,
                        fldFValor3=d.fldFValor3))
    cap = Capture(id=capture.id,
                  fkOwner=capture.fkOwner,
                  fldDTimeCreateTime=capture.fldDTimeCreateTime,
                  datos=res,
                  max_value=None)
    return cap


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
    movement2 = db.query(tbl_movement).filter(tbl_movement.fkOwner == movement.fkOwner).filter(
        tbl_movement.id != movement.id).first()
    if not movement2:
        raise HTTPException(status_code=404, detail="Movement 2 not found")
    capture.fkOwner = movement2.id
    db.commit()
    db.refresh(capture)
    return capture


@router.post("/label/", response_model=schemas.Capture)
def change_label(
        *,
        captura: int,
        movimiento: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    capture = crud.capture.get(db=db, id=captura)
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    movement = crud.movement.get(db=db, id=movimiento)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    capture.fkOwner = movement.id
    db.commit()
    db.refresh(capture)
    return capture
