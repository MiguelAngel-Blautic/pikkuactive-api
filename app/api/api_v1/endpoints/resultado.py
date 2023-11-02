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
from app.models import tbl_sesion, tbl_user
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
    texto = "select s.id, u.id, u.fldSFullName, um.fkTipo, e.fkEjercicio, e.id, hv.id, hv.fldFValor, hv.fldDTimeFecha, hv.fldFUmbral, hv.fldNIntento " \
            "from tbl_historico_valores hv " \
            "join tbl_umbrales um on (hv.fkUmbral = um.id) " \
            "join tbl_ejercicio e on (um.fkEjercicio = e.id) " \
            "join tbl_sesion s on (e.fkSesion = s.id) " \
            "join tbl_user u on (u.id = hv.fkUser) " \
            "where e.fkEjercicio is not NULL " \
            "and s.fkCreador = "+str(current_user.id)
    if sesion > 0:
        texto = texto + " and s.id = "+str(sesion)
    if user > 0:
        texto = texto + " and u.id = "+str(user)
    if tumbral > 0:
        texto = texto + " and um.fkTipo = "+str(tumbral)
    texto = texto + " and hv.fldDTimeFecha between '" + str(inicio) + "' and '" + str(fin) + "' order by s.id, u.id, u.fldSFullName, um.fkTipo, e.fkEjercicio, e.id, hv.id, hv.fldDTimeFecha, hv.fldFValor, hv.fldFUmbral, hv.fldNIntento"
    print(texto)
    sql_text = text(texto)
    res = db.execute(sql_text)
    sesiones = []
    if res.rowcount > 0:
        resultados = []
        ejercicios = []
        umbrales = []
        usuarios = []
        first = True
        for row in res:
            if first:
                idSesion = row[0]
                idUsuario = row[1]
                nombreUsuario = row[2]
                idUmbral = row[3]
                idEjercicio = row[4]
                first = False
            if idSesion != row[0]:
                ejercicios.append(ResultadoEjercicio(id=row[4], nombre="", resultados=resultados))
                resultados = []
                idEjercicio = row[4]
                umbrales.append(ResultadoTUmbral(id=row[3], ejercicios=ejercicios))
                ejercicios = []
                idUmbral = row[3]
                usuarios.append(ResultadoUsuario(id=row[1], nombre=row[2], tumbrales=umbrales))
                umbrales = []
                idUsuario = row[1]
                nombreUsuario = row[2]
                sesiones.append(ResultadosSesion(id=row[0], usuarios=usuarios))
                usuarios = []
                idSesion = row[0]
            if idUsuario != row[1]:
                ejercicios.append(ResultadoEjercicio(id=row[4], nombre="", resultados=resultados))
                resultados = []
                idEjercicio = row[4]
                umbrales.append(ResultadoTUmbral(id=row[3], ejercicios=ejercicios))
                ejercicios = []
                idUmbral = row[3]
                usuarios.append(ResultadoUsuario(id=row[1], nombre=row[2], tumbrales=umbrales))
                umbrales = []
                idUsuario = row[1]
                nombreUsuario = row[2]
            if idUmbral != row[3]:
                ejercicios.append(ResultadoEjercicio(id=row[4], nombre="", resultados=resultados))
                resultados = []
                idEjercicio = row[4]
                umbrales.append(ResultadoTUmbral(id=row[3], ejercicios=ejercicios))
                ejercicios = []
                idUmbral = row[3]
            if idEjercicio != row[4]:
                ejercicios.append(ResultadoEjercicio(id=row[4], nombre="", resultados=resultados))
                resultados = []
                idEjercicio = row[4]
            resultados.append(Resultado(id=row[6], fldFValor=row[7], fldDTimeFecha=row[8], fldNIntento=row[10], fldFUmbral=row[9], fkUser=row[1]))
        ejercicios.append(ResultadoEjercicio(id=idEjercicio, nombre="", resultados=resultados))
        umbrales.append(ResultadoTUmbral(id=idUmbral, ejercicios=ejercicios))
        usuarios.append(ResultadoUsuario(id=idUsuario, nombre=nombreUsuario, tumbrales=umbrales))
        sesiones.append(ResultadosSesion(id=idSesion, usuarios=usuarios))
    return sesiones


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
