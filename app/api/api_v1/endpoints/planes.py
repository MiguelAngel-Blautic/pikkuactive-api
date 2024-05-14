from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.users import read_user_by_id_plataforma
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes

router = APIRouter()

@router.get("/platform/", response_model=List[schemas.Plan])
def read_planes_by_user_plataforma(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    user = read_user_by_id_plataforma(user_id=user_id, db=db, current_user=current_user)
    return read_planes_by_user(user_id=user.id, db=db, current_user=current_user)


@router.get("/", response_model=List[schemas.Plan])
def read_planes_by_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    planes = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.fkCliente == user_id).all()
    return planes


@router.get("/{id}", response_model=schemas.Plan)
def read_planes_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    plan = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    return plan


@router.post("/platform/", response_model=schemas.Plan)
def create_plan_plataforma(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    user = read_user_by_id_plataforma(user_id=plan_in.fkCliente, db=db, current_user=current_user)
    plan_in.fkCliente = user.id
    return create_plan(db=db, plan_in=plan_in, current_user=current_user)


@router.post("/", response_model=schemas.Plan)
def create_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    newPlan = tbl_planes(fldSNombre=plan_in.fldSNombre,
                        fkCreador=current_user.id,
                        fkCliente=plan_in.fkCliente)
    db.add(newPlan)
    db.commit()
    db.refresh(newPlan)
    return newPlan


@router.put("/{id}", response_model=schemas.Plan)
def update_plan(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    plan = read_planes_by_id(id=id, db=db, current_user=current_user)
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    plan.fldSNombre = plan_in.fldSNombre
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{id}")
def delete_plan(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    plan = read_planes_by_id(id=id, db=db, current_user=current_user)
    db.delete(plan)
    db.commit()
    return
