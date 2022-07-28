from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.models import read_models, read_model
from app.api.api_v1.endpoints.movements import read_movement

router = APIRouter()


@router.get("/", response_model=List[schemas.Capture])
def read_captures(
        id_model: int,
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        pending: bool = False,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve captures.
    """
    model = read_model(db=db, id=id_model, current_user=current_user)
    if pending:
        movements = db.query(models.tbl_movement).filter(models.tbl_movement.fkOwner == model.id).all()
        ids_movements = [mov.id for mov in movements]
        version_last = db.query(models.tbl_version).filter(models.tbl_version.fkOwner == model.id).order_by(
            desc(models.tbl_version.fldDTimeCreateTime)).first()
        if version_last is None:
            captures = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).all()
        else:
            captures = db.query(models.tbl_capture).filter(and_(models.tbl_capture.fkOwner.in_(ids_movements),
                                                                models.tbl_capture.fldDTimeCreateTime > version_last.fldDTimeCreateTime)).all()
    else:
        captures = crud.capture.get_all_by_model(
            db=db, model=model, skip=skip, limit=limit
        )
    return captures


@router.get("/count", response_model=int)
def count_captures(
        id_model: int,
        db: Session = Depends(deps.get_db),
        pending: bool = False,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Count captures.
    """
    model = read_model(db=db, id=id_model, current_user=current_user)
    movements = db.query(models.tbl_movement).filter(models.tbl_movement.fkOwner == model.id).all()
    ids_movements = [mov.id for mov in movements]
    if pending:
        version_last = db.query(models.tbl_version).filter(models.tbl_version.fkOwner == model.id).order_by(
            desc(models.tbl_version.fldDTimeCreateTime)).first()
        if version_last is None:
            captures = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).count()
        else:
            captures = db.query(models.tbl_capture).filter(and_(models.tbl_capture.fkOwner.in_(ids_movements),
                                                                models.tbl_capture.fldDTimeCreateTime > version_last.fldDTimeCreateTime)).count()
    else:
        captures = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).count()
    return captures


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
    movement = read_movement(db=db, id=id_movement, current_user=current_user)
    # comprobar tamaño de la los datos segun el tiempo y el numero de dispositivos 
    # size_data = movement
    # if movementlen(capture_in.data)

    capture = crud.capture.create_with_owner(db=db, obj_in=capture_in, movement=movement)
    capture.ecg = []
    capture.mpu = []
    return capture


#
# @router.put("/{id}", response_model=schemas.Capture)
# def update_capture(
#         *,
#         db: Session = Depends(deps.get_db),
#         id: int,
#         capture_in: schemas.CaptureUpdate,
#         current_user: models.User = Depends(deps.get_current_active_user),
# ) -> Any:
#     """
#     Update an movement.
#     """
#     capture = read_capture(db=db, id=id, current_user=current_user)
#     capture = crud.capture.update(db=db, db_obj=capture, obj_in=capture_in)
#     return capture


@router.get("/{id}", response_model=schemas.Capture)
def read_capture(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get capture by ID.
    """
    capture = crud.capture.get(db=db, id=id)
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    # Check owner is current_user
    read_movement(db=db, id=capture.fkOwner, current_user=current_user)
    return capture


@router.delete("/{id}", response_model=schemas.Capture)
def delete_capture(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an capture.
    """
    read_capture(db=db, id=id, current_user=current_user)
    capture = crud.capture.remove(db=db, id=id)
    return capture
