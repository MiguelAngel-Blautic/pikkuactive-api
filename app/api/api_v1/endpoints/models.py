from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_model

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
    return model


@router.put("/{id}", response_model=schemas.Model)
def update_model(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    model_in: schemas.ModelUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an model.
    """
    model = read_model(db=db, id=id, current_user=current_user)  # Check model exists
    model = crud.model.update(db=db, db_obj=model, obj_in=model_in)
    return model


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
    if not crud.user.is_superuser(current_user) and (model.fkOwner != current_user.id) and not(crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id) and not(crud.model.pertenece(db=db, user=current_user.id, model=model.id))):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return model


@router.delete("/{id}", response_model=schemas.Model)
def delete_model(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an model.
    """
    read_model(db=db, id=id, current_user=current_user)  # Check model exists
    model = crud.model.remove(db=db, id=id)
    return model
