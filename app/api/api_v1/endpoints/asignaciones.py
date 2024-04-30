from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_planes, tbl_user
from app.models.tbl_planes import tbl_planes

router = APIRouter()


@router.post("/entrenar", response_model=int)
def entrenar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
        return 0


@router.put("/entrenar", response_model=int)
def entrenar(
        *,
        db: Session = Depends(deps.get_db),
        profesional: int,
        usuario: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
        return 0


@router.delete("/entrenar", response_model=int)
def entrenar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
        return 0


@router.delete("/plan")
def asignar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    return 0
