from datetime import datetime
from typing import Any, List

import sqlalchemy
from DateTime import DateTime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import now

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.ejercicio import read_ejercicio
from app.api.api_v1.endpoints.umbral import read_umbral
from app.models import tbl_sesion
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.schemas import Resultado, ResultadosSesion, ResultadoUsuario, ResultadoTUmbral, ResultadoEjercicio

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


@router.get("/lista/", response_model=List[schemas.ResultadosSesion])
def read_resultado(
        *,
        db: Session = Depends(deps.get_db),
        sesion: int = 0,
        user: int = 0,
        tumbral: int = 0,
        inicio: str,
        fin: str,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    resultado = []
    texto = "select s.id, u.id, um.fkTipo, m.id, e.id, u.fldSFullName, hv.fldFValor, hv.fldDTimeFecha, hv.fldFUmbral, m.fldSName, hv.fldNIntento " \
            "from tbl_historico_valores hv left join tbl_umbrales um on (um.id = hv.fkUmbral) left join tbl_ejercicio e on (e.id = um.fkEjercicio) " \
            "left join tbl_model m on (m.id = e.fkEjercicio) left join tbl_sesion s on (s.id = e.fkSesion) left join tbl_user u on " \
            "(u.id = hv.fkUser) where "
    if sesion > 0:
        texto = texto + "s.id = " + str(sesion) + " and "
    if user > 0:
        texto = texto + "u.id = " + str(user) + " and "
    if tumbral > 0:
        texto = texto + "um.fkTipo = " + str(tumbral) + " and "
    texto = texto + "hv.fldDTimeFecha between '" + str(inicio) + "' and '" + str(
        fin) + "' order by s.id, u.id, um.fkTipo, m.id, e.id, u.fldSFullName, hv.fldFValor, hv.fldDTimeFecha, " \
               "hv.fldFUmbral, m.fldSName, hv.fldNIntento "
    sql_text = text(texto)
    res = db.execute(sql_text)
    first = True
    sesionId = 0
    usuarioId = 0
    usuarioN = 0
    usuarioL = []
    tumbralId = 0
    tumbralL = []
    ejercicioId = 0
    ejercicioN = 0
    ejercicioL = []
    resultadoL = []
    if res.rowcount > 0:
        for row in res:
            if first:
                print("Primero")
                sesionId = row[0]
                usuarioId = row[1]
                usuarioN = row[5]
                usuarioL = []
                tumbralId = row[2]
                tumbralL = []
                if row[9]:
                    ejercicioN = row[9]
                else:
                    ejercicioN = "Generico"
                if row[3]:
                    ejercicioId = row[3]
                else:
                    ejercicioId = row[4]
                ejercicioL = []
                resultadoL = []
                first = False
            if row[0] != sesionId:
                print("Nueva sesion")
                ejercicioL.append(ResultadoEjercicio(id=ejercicioId, nombre=ejercicioN, resultados=resultadoL))
                tumbralL.append(ResultadoTUmbral(id=tumbralId, ejercicios=ejercicioL))
                usuarioL.append(ResultadoUsuario(id=usuarioId, nombre=usuarioN, tumbrales=tumbralL))
                resultado.append(ResultadosSesion(id=sesionId, usuarios=usuarioL))
                sesionId = row[0]
                usuarioN = row[5]
                usuarioL = []
                usuarioId = row[1]
                tumbralId = row[2]
                tumbralL = []
                if row[9]:
                    ejercicioN = row[9]
                else:
                    ejercicioN = "Generico"
                if row[3]:
                    ejercicioId = row[3]
                else:
                    ejercicioId = row[4]
                ejercicioL = []
                resultadoL = []
            if row[1] != usuarioId:
                print("    Nuevo usuario")
                ejercicioL.append(ResultadoEjercicio(id=ejercicioId, nombre=ejercicioN, resultados=resultadoL))
                tumbralL.append(ResultadoTUmbral(id=tumbralId, ejercicios=ejercicioL))
                usuarioL.append(ResultadoUsuario(id=usuarioId, nombre=usuarioN, tumbrales=tumbralL))
                usuarioN = row[5]
                usuarioId = row[1]
                tumbralId = row[2]
                tumbralL = []
                if row[9]:
                    ejercicioN = row[9]
                else:
                    ejercicioN = "Generico"
                if row[3]:
                    ejercicioId = row[3]
                else:
                    ejercicioId = row[4]
                ejercicioL = []
                resultadoL = []
            if row[2] != tumbralId:
                print("        Nuevo umbral")
                ejercicioL.append(ResultadoEjercicio(id=ejercicioId, nombre=ejercicioN, resultados=resultadoL))
                tumbralL.append(ResultadoTUmbral(id=tumbralId, ejercicios=ejercicioL))
                tumbralId = row[2]
                if row[9]:
                    ejercicioN = row[9]
                else:
                    ejercicioN = "Generico"
                if row[3]:
                    ejercicioId = row[3]
                else:
                    ejercicioId = row[4]
                ejercicioL = []
                resultadoL = []
            if row[3] != ejercicioId:
                print("            Nuevo ejercicio")
                ejercicioL.append(ResultadoEjercicio(id=ejercicioId, nombre=ejercicioN, resultados=resultadoL))
                if row[9]:
                    ejercicioN = row[9]
                else:
                    ejercicioN = "Generico"
                if row[3]:
                    ejercicioId = row[3]
                else:
                    ejercicioId = row[4]
                resultadoL = []
            valor = Resultado(id=row[4], ldFValor=row[6], fldDTimeFecha=row[7], fldNIntento=row[10], fldFUmbral=row[8], fkUser=row[1])
            resultadoL.append(valor)
        ejercicioL.append(ResultadoEjercicio(id=ejercicioId, nombre=ejercicioN, resultados=resultadoL))
        tumbralL.append(ResultadoTUmbral(id=tumbralId, ejercicios=ejercicioL))
        usuarioL.append(ResultadoUsuario(id=usuarioId, nombre=usuarioN, tumbrales=tumbralL))
        resultado.append(ResultadosSesion(id=sesionId, usuarios=usuarioL))
    return resultado


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
