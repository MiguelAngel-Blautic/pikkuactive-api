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
from app.schemas.resultados import DatoResultado, EjercicioResultado

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

@router.get("/{id}")
def get_datos_ejercicio(
    ejercicioId: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    registros = [r for r in db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == ejercicioId).all()]
    res = []

    registroEstado = [r.id for r in registros if r.fkTipoDato == 0]
    estados = [r for r in db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroEstado[0]).all()]
    registroRepeticiones = [r.id for r in registros if r.fkTipoDato == 6]
    repeticiones = [r for r in db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroRepeticiones[0]).all()]
    registroIntentos = [r.id for r in registros if r.fkTipoDato == 7]
    intentos = [r for r in db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroIntentos[0]).all()]
    registroVelocidad = [r.id for r in registros if r.fkTipoDato == 13]
    velocidad = [r for r in db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroVelocidad[0]).all()]
    registroHr = [r.id for r in registros if r.fkTipoDato == 3]
    hr = [r for r in db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroHr[0]).all()]
    registroAi = [r.id for r in registros if r.fkTipoDato == 12]
    ai = [r for r in db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroAi[0]).all()]

    for e in estados:
        repeticiones1 = [DatoResultado(value=r.fldFValor, date=r.fldDTime) for r in repeticiones if r.fldDTime <= e.fldDTime]
        intentos1 = [DatoResultado(value=r.fldFValor, date=r.fldDTime) for r in intentos if r.fldDTime <= e.fldDTime]
        velocidad1 = [DatoResultado(value=r.fldFValor, date=r.fldDTime) for r in velocidad if r.fldDTime <= e.fldDTime]
        hr1 = [DatoResultado(value=r.fldFValor, date=r.fldDTime) for r in hr if r.fldDTime <= e.fldDTime]
        ai1 = [DatoResultado(value=r.fldFValor, date=r.fldDTime) for r in ai if r.fldDTime <= e.fldDTime]
        momentosRep = [m.date for m in repeticiones1 + intentos1]
        reps = []
        ints = []
        for m in momentosRep:
            reps.append(DatoResultado(value=len([r for r in repeticiones1 if r.date <= m]), date=m))
            ints.append(DatoResultado(value=len([r for r in intentos1 if r.date <= m]), date=m))
        res.append(EjercicioResultado(
            repeticiones=reps,
            intentos=ints,
            velocidad=velocidad1,
            heartRate=hr1,
            activityIndex=ai1
        ))
    return res


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




























