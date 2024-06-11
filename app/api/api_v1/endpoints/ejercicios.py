import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from app import models, schemas
from app.api import deps
from app.models import tbl_ejercicios
from app.models.tbl_ejercicios import tbl_sesion, tbl_dato, tbl_marcas
from app.schemas import Sesion, Dato, Marca

router = APIRouter()


@router.put("/")
def add_sesion(
        *,
        sesion: Sesion,
        db: Session = Depends(deps.get_db),
        background_tasks: BackgroundTasks
) -> Any:
    print("INICIADO")
    background_tasks.add_task(completarSesion, sesion, db)
    return json.loads('{"msg": "OK"}')


def completarSesion(sesion: Sesion, db: Session):
    new_sesion = tbl_sesion(fldDInicio=sesion.inicio,
                            fldNEdad=sesion.edad,
                            fldFAltura=sesion.altura,
                            fldFPeso=sesion.peso,
                            fldNSexo=sesion.sexo)
    db.add(new_sesion)
    db.commit()
    db.refresh(new_sesion)
    id = new_sesion.id
    print("SESION")
    i = 0
    j = 0
    for d in sesion.datos:
        new_dato = tbl_dato(fkSensor = d.sensor,
                            fkSesion = id,
                            fldDTime = d.hora,
                            fldFValor = d.valor)
        db.add(new_dato)
        i = i + 1
        j = j + 1
        if(j >= 1000):
            j = 0
            print(str(i)+"/"+str(len(sesion.datos)))
            db.commit()
    print("DATOS")
    i = 0
    j = 0
    for e in sesion.etiquetas:
        new_marca = tbl_marcas(fldNTipo = 2,
                               fldNValor = e.valor,
                               fldDTime = e.hora,
                               fkSesion = id)
        db.add(new_marca)
        i = i + 1
        j = j + 1
        if(j >= 1000):
            j = 0
            print(str(i)+"/"+str(len(sesion.etiquetas)))
            db.commit()
    print("MARCAS")
    i = 0
    j = 0
    for e in sesion.fases:
        new_marca = tbl_marcas(fldNTipo = 1,
                               fldNValor = e.valor,
                               fldDTime = e.hora,
                               fkSesion = id)
        db.add(new_marca)
        i = i + 1
        j = j + 1
        if(j >= 1000):
            j = 0
            print(str(i)+"/"+str(len(sesion.fases)))
            db.commit()
    print("FASES")
    db.commit()
    print("COMMITED")
    return json.loads('{"id": '+str(id)+'}')


@router.get("/")
def get_sesiones(
        *,
        db: Session = Depends(deps.get_db)
) -> Any:
    return db.query(tbl_sesion).all()


@router.get("/{id}")
def get_sesiones(
        *,
        id: int,
        db: Session = Depends(deps.get_db)
) -> Any:
    sesion = db.query(tbl_sesion).get(id)
    if not sesion:
        raise HTTPException(status_code=404, detail="The session doesn't exist")
    datos = []
    datosDB = db.query(tbl_dato).filter(tbl_dato.fkSesion == id).all()
    for d in datosDB:
        datos.append(Dato(sensor=d.fkSensor, valor=d.fldFValor, hora=d.fldDTime))
    etiquetas = []
    etiquetasDB = db.query(tbl_marcas).filter(tbl_marcas.fkSesion == id).filter(tbl_marcas.fldNTipo == 2).all()
    for e in etiquetasDB:
        etiquetas.append(Marca(valor=e.fldNValor, hora=e.fldDTime))
    fases = []
    fasesDB = db.query(tbl_marcas).filter(tbl_marcas.fkSesion == id).filter(tbl_marcas.fldNTipo == 1).all()
    for f in fasesDB:
        fases.append(Marca(valor=f.fldNValor, hora=f.fldDTime))
    return Sesion(edad=sesion.fldNEdad, altura=sesion.fldFAltura, peso=sesion.fldFPeso, sexo=sesion.fldNSexo, inicio=sesion.fldDInicio, datos=datos, fases=fases, etiquetas=etiquetas)







