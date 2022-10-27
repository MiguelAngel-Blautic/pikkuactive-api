from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.ejercicio import read_ejercicio
from app.api.api_v1.endpoints.umbral import read_umbral
from app.models import tbl_sesion
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.models.tbl_sesion import tbl_planes
from app.api.api_v1.endpoints.plan import read_plan, check_permission
from app.schemas import Graficas

router = APIRouter()


@router.get("/", response_model=List[schemas.Resultado])
def read_resultados(
        db: Session = Depends(deps.get_db),
        umbral_id: int = 0,
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    umbral = read_umbral(db=db, id=umbral_id, current_user=current_user)
    resultado: List[tbl_historico_valores] = crud.resultado.get_multi_valores(db=db, umbral=umbral.id, skip=skip, limit=limit)
    return resultado


@router.post("/", response_model=schemas.Resultado)
def create_resultado(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        resultado_in: schemas.ResultadoCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    resultado_in.fldDTimeFecha = datetime.today()
    umbral = crud.umbral.get(db=db, id=id)
    if not umbral:
        raise HTTPException(status_code=404, detail="Umbral not found")
    resultado = crud.resultado.create_with_owner(db=db, db_obj=umbral, obj_in=resultado_in)
    return resultado


@router.put("/{id}", response_model=schemas.Resultado)
def update_resultado(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        resultado_in: schemas.ResultadoUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an model.
    """
    resultado = read_resultado(db=db, id=id, current_user=current_user)  # Check model exists
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado not found")
    resultado = crud.resultado.update(db=db, db_obj=resultado, obj_in=resultado_in)
    return resultado


@router.get("/{id}", response_model=schemas.Resultado)
def read_resultado(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    resultado = crud.resultado.get(db=db, id=id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado not found")
    umbral = read_umbral(db=db, id=resultado.fkUmbral, current_user=current_user)
    if not umbral:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return resultado


@router.get("/graficas/{id}", response_model=schemas.Graficas)
def leer_graficas(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user)
) -> Any:
    graficas = crud.resultado.get_graficas(db=db, user=id, profesional=current_user.id)
    print(graficas)
    return graficas



@router.delete("/{id}", response_model=schemas.Resultado)
def delete_resultado(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an model.
    """
    read_resultado(db=db, id=id, current_user=current_user)  # Check model exists
    resultado = crud.resultado.get(db=db, id=id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Umbral not found")
    resultado = crud.resultado.remove(db=db, id=id)
    return resultado
