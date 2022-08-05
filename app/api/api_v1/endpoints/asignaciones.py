from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.ejercicio import read_ejercicio
from app.api.api_v1.endpoints.umbral import read_umbral
from app.models import tbl_plan, tbl_user
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.models.tbl_plan import tbl_planes
from app.api.api_v1.endpoints.plan import read_plan, check_permission

router = APIRouter()


@router.get("/centros", response_model=List[schemas.User])
def read(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    resultado: List[tbl_user] = crud.user.get_centros(db=db, skip=skip, limit=limit)
    return resultado


@router.get("/profesionales", response_model=List[schemas.User])
def read(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    resultado: List[tbl_user] = crud.user.get_profesionales(db=db, skip=skip, limit=limit, user=current_user)
    return resultado


@router.get("/pacientes", response_model=List[schemas.User])
def read(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    resultado: List[tbl_user] = crud.user.get_pacientes(db=db, skip=skip, limit=limit, user=current_user)
    return resultado


@router.put("/entrenar", response_model=schemas.Entrena)
def entrenar(
        *,
        db: Session = Depends(deps.get_db),
        entrena_in: schemas.EntrenaCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    if not (entrena_in.fkUsuario == current_user.id or entrena_in.fkProfesional == current_user.id):
        raise HTTPException(status_code=400, detail="Not involved")
    resultado = crud.entrena.create_with_owner(db=db, obj_in=entrena_in, user=current_user)
    return resultado


@router.delete("/entrenar", response_model=schemas.Entrena)
def entrenar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    entrena = crud.entrena.get(db=db, id=id)
    if not entrena:
        raise HTTPException(status_code=404, detail="Relation not found")
    if current_user.fkRol < 2:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    if not (entrena.fkUsuario == current_user.id or entrena.fkProfesional == current_user.id):
        raise HTTPException(status_code=400, detail="Not involved")
    entrena = crud.entrena.remove(db=db, id=id)
    return entrena


@router.put("/plan", response_model=schemas.Asignado)
def asignar(
        *,
        db: Session = Depends(deps.get_db),
        entrena_in: schemas.AsignadoCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.fkRol > 1:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    plan = read_plan(db=db, id=entrena_in.fkPlan, current_user=current_user)  # Check model exists
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.fkCreador != current_user.id:
        raise HTTPException(status_code=400, detail="Not involved")
    return crud.asignado.create_with_validation(db=db, obj_in=entrena_in, user=current_user)


@router.delete("/plan", response_model=schemas.Asignado)
def asignar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    asignacion = crud.asignado.get(db=db, id=id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Relation not found")
    if current_user.fkRol < 2:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    if not (asignacion.fkUsuario == current_user.id or asignacion.fkAsignador == current_user.id):
        raise HTTPException(status_code=400, detail="Not involved")
    asignacion = crud.asignado.remove(db=db, id=id)
    return asignacion