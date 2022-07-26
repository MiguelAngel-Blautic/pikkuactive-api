from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException

router = APIRouter()


@router.get("/", response_model=str)
def test() -> any:
    return "hola"
