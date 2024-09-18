from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.tbl_position import tbl_position

router = APIRouter()


@router.get("/", response_model=List[schemas.Position])
def read_positions(
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Retrieve positions.
    """
    positions = crud.position.get_multi(db=db)
    db.close()
    return positions