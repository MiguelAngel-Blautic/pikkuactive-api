from typing import Any, List
import sqlalchemy as db
from fastapi import APIRouter, Body, Depends, HTTPException

router = APIRouter()


@router.get("/", response_model=str)
def test(
        id: int,
) -> Any:
    return id
