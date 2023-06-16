from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_model, tbl_capture, tbl_movement
from app.schemas import MovementCreate
from app.schemas.movement import MovementCaptures

router = APIRouter()


@router.get("/", response_model=List[schemas.Model])
def read_models(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    if crud.user.is_superuser(current_user):
        model: List[tbl_model] = crud.model.get_multi(db, skip=skip, limit=limit)
    else:
        model = crud.model.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return model


@router.post("/", response_model=schemas.Model)
def create_model(
    *,
    db: Session = Depends(deps.get_db),
    model_in: schemas.ModelCreate,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new model.
    """
    model = crud.model.create_with_owner(db=db, obj_in=model_in, owner_id=current_user.id)
    movement_correct = MovementCreate(fldSLabel=model.fldSName, fldSDescription=model.fldSName)
    crud.movement.create_with_owner(db=db, obj_in=movement_correct, fkOwner=model.id)
    movement_incorrect = MovementCreate(fldSLabel="Other", fldSDescription="Other")
    crud.movement.create_with_owner(db=db, obj_in=movement_incorrect, fkOwner=model.id)
    return model


@router.delete("/")
def delete_model(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete existing model
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id))):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    db.delete(model)
    db.commit()
    return 1


@router.get("/{id}", response_model=schemas.Model)
def read_model(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id))):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return model


@router.get("/capturas/{id}", response_model=schemas.MovementCaptures)
def count_captures(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Devuelve el numero de capturas de 'Movement' y de 'Other'
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id))):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    movements = db.query(tbl_movement).filter(tbl_movement.fkOwner == model.id).all()
    captures1 = db.query(tbl_capture).filter(tbl_capture.fkOwner == movements[0].id).all()
    captures2 = db.query(tbl_capture).filter(tbl_capture.fkOwner == movements[1].id).all()
    res = MovementCaptures(movement=len(captures1), other=len(captures2))
    return res
