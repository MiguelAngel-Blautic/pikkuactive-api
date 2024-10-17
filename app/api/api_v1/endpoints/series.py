from statistics import mean
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import ejercicios
from app.api.api_v1.endpoints.ejercicios import read_valores_ejercicios, read_ejercicios_by_id_serie_detalle
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_series, tbl_entrenamientos
from app.schemas import ResumenEstadistico
from app.schemas.ejercicio import Resultado, EjercicioDetalles

router = APIRouter()


def read_valores_series(
    *,
    db: Session,
    bloque: int,
) -> Any:
    series = db.query(tbl_series).filter(tbl_series.fkBloque == bloque).all()
    res = []
    for s in series:
        ejercicios = read_valores_ejercicios(db=db, serie=s.id)
        adh = (sum(e.adherencia for e in ejercicios) / len(ejercicios)) / s.fldNRepeticiones
        res.append(Resultado(id=s.id, nombre=s.fldSDescripcion, adherencia=adh, completo=100))
    return res


def read_series_by_id_detalle(
        id: int,
        generico: int,
        db: Session
) -> Any:
    res = []
    series = db.query(tbl_series).filter(tbl_series.fkBloque == id).all()
    for serie in series:
        finalizado = 0
        if not serie:
            raise HTTPException(status_code=404, detail="The serie doesn't exist")
        adherencias = []
        ejercicios = read_ejercicios_by_id_serie_detalle(serie.id, generico, db)
        duraciones = [e.duracion for e in ejercicios]
        durTotal = sum(duraciones)
        adherencia = 0
        for ejer in ejercicios:
            if serie.fldNRepeticiones >= 1:
                ejer.adherencia = ejer.adherencia / serie.fldNRepeticiones
            else:
                ejer.adherencia = 0
            adherencias.append(ejer.adherencia)
            if ejer.isresults == 1:
                finalizado = 1
        if len(adherencias) > 0 and durTotal > 0:
            for i in range(len(adherencias)):
                adherencia = adherencia + (adherencias[i] * duraciones[i] / durTotal)
        res.append(EjercicioDetalles(
            fldNOrden=serie.fldNOrden,
            fldNDescanso=serie.fldNDescanso,
            fldNRepeticiones=serie.fldNRepeticiones,
            fldNDuracion=0,
            fldNDuracionEfectiva=0,
            fldFVelocidad=0,
            fkModelo=0,
            fldSToken="",
            id=serie.id,
            duracion = durTotal,
            adherencia=adherencia,
            items=ejercicios,
            tipo=4,
            completo=0,
            nombre=serie.fldSDescripcion,
            isresults=finalizado,
            issumultanea=serie.fldBSimultanea
        ))
    return res

@router.post("/list", response_model=List[schemas.ResumenEstadistico])
def read_series_by_id_bloque(
        bloque: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sql = text("""
        SELECT ts.fkPadre, ts2.fldSDescripcion , sum(te.fldNRepeticioneS * ts.fldNRepeticiones)
from tbl_ejercicios te
    join tbl_series ts on (ts.id = te.fkSerie) join tbl_series ts2 on (ts2.id = ts.fkPadre)
   WHERE ts2.fkBloque = """+str(bloque)+""" group by ts.fkPadre; """)
    res = db.execute(sql)
    adherencia = 0
    for row in res:
        sql = text("""
        SELECT count(*)
            from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
            join tbl_series ts on (ts.id = te.fkSerie)
            where ts.fkPadre=""" + str(row[0]) + """ and tre.fkTipoDato = 2;""")
        total = db.execute(sql)
        for t in total:
            adherencia = (t[0] * 100) / row[2]
        entrada = ResumenEstadistico(
            tipo=4,
            nombre=row[1],
            adherencia=adherencia,
            completo=0,
            id=row[0],
        )
        response.append(entrada)
    db.close()
    return response


@router.get("/", response_model=List[schemas.Serie])
def read_series_by_bloque_server(
    bloque_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_series_by_bloque(bloque_id, db, current_user)
    db.close()
    return res


def read_series_by_bloque(
        bloque_id: int,
        db: Session,
        current_user: models.tbl_user,
) -> Any:
    if current_user.fkRol == 2:
        bloque = db.query(tbl_bloques).get(bloque_id)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if not plan:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
        series = db.query(tbl_series).filter(tbl_series.fkBloque == bloque_id).all()
    else:
        series = db.query(tbl_series).filter(tbl_series.fkCreador == current_user.id).filter(tbl_series.fkBloque == bloque_id).all()
    return series


@router.get("/{id}", response_model=schemas.Serie)
def read_series_by_id_server(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_series_by_id(id, db, current_user)
    db.close()
    return res


def read_series_by_id(
        id: int,
        db: Session,
        current_user: models.tbl_user,
) -> Any:
    serie = db.query(tbl_series).filter(tbl_series.id == id).first()
    if not serie:
        raise HTTPException(status_code=404, detail="The serie doesn't exist")
    if current_user.fkRol == 2:
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return serie


@router.post("/", response_model=schemas.Serie)
def create_serie(
    *,
    db: Session = Depends(deps.get_db),
    serie_in: schemas.SerieCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    series = read_series_by_bloque(db=db, current_user=current_user, bloque_id=serie_in.fkBloque)
    newSerie = tbl_series(fldSDescripcion=serie_in.fldSDescripcion,
                        fkCreador=current_user.id,
                        fkBloque=serie_in.fkBloque,
                        fldNDescanso=serie_in.fldNDescanso,
                        fldNOrden=len(series)+1,
                        fldNRepeticiones=serie_in.fldNRepeticiones,
                        fldBSimultanea=serie_in.fldBSimultanea)
    db.add(newSerie)
    db.commit()
    db.refresh(newSerie)
    db.close()
    return newSerie


@router.put("/{id}", response_model=schemas.Serie)
def update_serie(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    serie_in: schemas.SerieUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    serie = read_series_by_id(id=id, db=db, current_user=current_user)
    if not serie:
        raise HTTPException(status_code=404, detail="The block doesn't exist")
    serie.fldSDescripcion = serie_in.fldSDescripcion
    serie.fldNDescanso = serie_in.fldNDescanso
    serie.fldNRepeticiones = serie_in.fldNRepeticiones
    serie.fldBSimultanea = serie_in.fldBSimultanea
    db.commit()
    db.refresh(serie)
    db.close()
    return serie


@router.delete("/{id}")
def delete_serie(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    serie = read_series_by_id(id=id, db=db, current_user=current_user)
    change_order(serie.id, 0, current_user=current_user, db=db)
    db.delete(serie)
    db.commit()
    db.close()
    return


@router.post("/orden", response_model=schemas.Serie)
def change_order_server(
    serie_id: int,
    new_posicion: int = 0,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    res = change_order(serie_id, new_posicion, current_user, db)
    db.close()
    return res


def change_order(
        serie_id: int,
        new_posicion: int,
        current_user: models.tbl_user,
        db: Session,
) -> Any:
    """
    Cambia la posicion de una serie
    """
    serie = read_series_by_id(id=serie_id, db=db, current_user=current_user)
    if new_posicion == 0:
        total_series = read_series_by_bloque(bloque_id=serie.fkBloque, db=db, current_user=current_user)
        new_posicion = len(total_series) + 1
    if(new_posicion > serie.fldNOrden):
        series = db.query(tbl_series).filter(tbl_series.fkBloque == serie.fkBloque).filter(tbl_series.fldNOrden > serie.fldNOrden).filter(tbl_series.fldNOrden <= new_posicion).all()
        for s in series:
            s.fldNOrden = s.fldNOrden - 1
        serie.fldNOrden = new_posicion
    else:
        series = db.query(tbl_series).filter(tbl_series.fkBloque == serie.fkBloque).filter(
            tbl_series.fldNOrden < serie.fldNOrden).filter(tbl_series.fldNOrden >= new_posicion).all()
        for s in series:
            s.fldNOrden = s.fldNOrden + 1
        serie.fldNOrden = new_posicion
    db.commit()
    db.refresh(serie)
    return serie


def clonar(
    old_bloque: int,
    new_bloque: int,
    db: Session,
) -> Any:
    series = db.query(tbl_series).filter(tbl_series.fkBloque == old_bloque).all()
    for obj in series:
        new = tbl_series(fldSDescripcion=obj.fldSDescripcion,
                        fkBloque=new_bloque,
                        fldNRepeticiones=obj.fldNRepeticiones,
                        fldNDescanso=obj.fldNDescanso,
                        fldNOrden=obj.fldNOrden,
                        fkCreador=obj.fkCreador,
                        fkPadre=obj.id)
        db.add(new)
        db.commit()
        db.refresh(new)
        ejercicios.clonar(old_serie=obj.id, new_serie=new.id, db=db)
    return


























