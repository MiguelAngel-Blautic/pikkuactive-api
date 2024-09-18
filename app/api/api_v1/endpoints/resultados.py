from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
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
    res = db.query(tbl_tipo_datos).all()
    db.close()
    return res


@router.get("/ejercicioGeneral/")
def read_datos_ejercicio_plan(
        plan: int,
        modelo: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    sql = text("""
                SELECT ttd.fldFNombre, tr.fldDTime, tr.fldFValor
                    from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) 
                    join tbl_tipo_datos ttd on (ttd.id = tre.fkTipoDato)
                    join tbl_ejercicios te on (te.id = tre.fkEjercicio) join tbl_series ts on (ts.id = te.fkSerie)
                    join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                    where te.fkModelo=""" + str(modelo) + """ and ten.fkPlan=""" + str(plan) + """
                    order by ttd.fldFNombre, tr.fldDTime, tr.fldFValor;""")
    resultados = db.execute(sql)
    lastNombre = ""
    listAux = []
    respuesta = []
    for res in resultados:
        if res[0] == "":
            lastNombre = res[0]
        if res[0] != lastNombre:
            respuesta.append({"nombre": lastNombre, "datos": listAux})
            lastNombre = res[0]
            listAux = []
        listAux.append({"date": res[1], "valor": res[2]})
    respuesta.append({"nombre": lastNombre, "datos": listAux})
    db.close()
    return respuesta


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
    db.close()
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
    db.close()
    return resDB

def clonar(
    old_ejercicio: int,
    new_ejercicio: int,
    db: Session,
) -> Any:
    registros = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == old_ejercicio).all()
    for r in registros:
        new = tbl_registro_ejercicios(fkTipoDato = r.fkTipoDato,
                                      fkEjercicio = new_ejercicio)
        db.add(new)
        db.commit()
        db.refresh(new)
    return




























