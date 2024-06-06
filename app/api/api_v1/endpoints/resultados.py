from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_series, tbl_ejercicios, tbl_entrenamientos, \
    tbl_tipo_datos, tbl_resultados
from app.models.tbl_resultados import tbl_registro_ejercicios
from app.schemas import Resultado

router = APIRouter()


@router.get("/")
def read_tipos_dato(
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    return db.query(tbl_tipo_datos).all()

@router.put("/tipodato/")
def add_tipodato(
    tipo: int,
    ejercicio: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    new = tbl_registro_ejercicios(fkEjercicio = ejercicio,
                                  fkTipoDato = tipo)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.put("/resultado/")
def add_dato(
    resultado: Resultado,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    resDB = tbl_resultados(fkRegistro=resultado.fkRegistro,
                           fldFValor = resultado.fldFValor,
                           fldDTime = resultado.fldDTime)
    db.add(resDB)
    db.commit()
    db.refresh(resDB)
    return resDB

def clonar(
    old_ejercicio: int,
    new_ejercicio: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    registros = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == old_ejercicio).all()
    for r in registros:
        new = tbl_registro_ejercicios(fkTipoDato = r.fkTipoDato,
                                      fkEjercicio = new_ejercicio)
        db.add(new)
        db.commit()
        db.refresh(new)
    return




























