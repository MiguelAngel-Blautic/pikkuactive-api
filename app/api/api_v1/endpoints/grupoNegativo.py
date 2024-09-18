from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.tbl_position import tbl_position

router = APIRouter()


@router.get("/", response_model=List[schemas.Grupo])
def read_grupos_negativos(
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve positions.
    """
    positions = crud.grupo.get_multi(db=db)
    db.close()
    return positions