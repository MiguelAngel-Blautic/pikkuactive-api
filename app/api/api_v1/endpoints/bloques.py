from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import entrenamientos, series
from app.api.api_v1.endpoints.series import read_valores_series
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_entrenamientos
from app.schemas import ResumenEstadistico
from app.schemas.ejercicio import Resultado

router = APIRouter()


@router.get("/", response_model=List[schemas.Bloque])
def read_bloques_by_entrenamiento(
    entrenamiento_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    if current_user.fkRol == 2:
        entrenamiento = db.query(tbl_entrenamientos).get(entrenamiento_id)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if not plan:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
        bloques = db.query(tbl_bloques).filter(
            tbl_bloques.fkEntrenamiento == entrenamiento_id).all()
    else:
        bloques = db.query(tbl_bloques).filter(tbl_bloques.fkCreador == current_user.id).filter(tbl_bloques.fkEntrenamiento == entrenamiento_id).all()
    return bloques


@router.post("/list", response_model=List[schemas.ResumenEstadistico])
def read_bloques_by_id_entrenamiento(
        entrenamiento: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sql = text("""
        SELECT tb.fkPadre, tb2.fldSDescripcion , sum(te.fldNRepeticioneS * ts.fldNRepeticiones)
from tbl_ejercicios te
    join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_bloques tb2 on (tb2.id = tb.fkPadre)
   WHERE tb2.fkEntrenamiento = """+str(entrenamiento)+""" group by tb.fkPadre; """)
    res = db.execute(sql)
    adherencia = 0
    actual = datetime.now()
    for row in res:
        diaAct = actual.date() - row[3]
        dias = row[4] - row[3]
        if dias.days <= 0:
            completado = (100 * diaAct.days)
        else:
            completado = (100 * diaAct.days) / dias.days
        sql = text("""
        SELECT count(*)
            from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
            join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque)
            where tb.fkPadre=""" + str(row[0]) + """ and tre.fkTipoDato = 2;""")
        total = db.execute(sql)
        for t in total:
            adherencia = (t[0] * 100) / row[2]
        entrada = ResumenEstadistico(
            tipo=3,
            nombre=row[1],
            adherencia=adherencia,
            completo=0,
            id=row[0],
        )
        response.append(entrada)
    return response


def read_valores_bloques(
    *,
    db: Session = Depends(deps.get_db),
    entrene: int,
) -> Any:
    bloques = db.query(tbl_bloques).filter(tbl_bloques.fkEntrenamiento == entrene).all()
    res = []
    for b in bloques:
        series = read_valores_series(db=db, bloque=b.id)
        adh = sum(s.adherencia for s in series) / len(series)
        res.append(Resultado(id=b.id, nombre=b.fldSDescripcion, adherencia=adh, completo=100))
    return res


@router.get("/{id}", response_model=schemas.Bloque)
def read_bloques_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    bloque = db.query(tbl_bloques).filter(tbl_bloques.id == id).first()
    if not bloque:
        raise HTTPException(status_code=404, detail="The block doesn't exist")
    if current_user.fkRol == 2:
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return bloque


@router.post("/", response_model=schemas.Bloque)
def create_bloque(
    *,
    db: Session = Depends(deps.get_db),
    bloque_in: schemas.BloqueCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    bloques = read_bloques_by_entrenamiento(db=db, current_user=current_user, entrenamiento_id=bloque_in.fkEntrenamiento)
    newBloque = tbl_bloques(fldSDescripcion=bloque_in.fldSDescripcion,
                        fkCreador=current_user.id,
                        fkEntrenamiento=bloque_in.fkEntrenamiento,
                        fldNDescanso=bloque_in.fldNDescanso,
                        fldNOrden=len(bloques)+1)
    db.add(newBloque)
    db.commit()
    db.refresh(newBloque)
    return newBloque


@router.put("/{id}", response_model=schemas.Bloque)
def bloque_plan(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    bloque_in: schemas.BloqueUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    bloque = read_bloques_by_id(id=id, db=db, current_user=current_user)
    if not bloque:
        raise HTTPException(status_code=404, detail="The block doesn't exist")
    bloque.fldSDescripcion = bloque_in.fldSDescripcion
    bloque.fldNDescanso = bloque_in.fldNDescanso
    db.commit()
    db.refresh(bloque)
    return bloque


@router.delete("/{id}")
def delete_bloque(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    bloque = read_bloques_by_id(id=id, db=db, current_user=current_user)
    change_order(bloque.id, 0, current_user=current_user, db=db)
    db.delete(bloque)
    db.commit()
    return


@router.post("/orden", response_model=schemas.Bloque)
def change_order(
    bloque_id: int,
    new_posicion: int = 0,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Cambia la posicion de un bloque
    """
    bloque = read_bloques_by_id(id=bloque_id, db=db, current_user=current_user)
    if new_posicion == 0:
        total_bloques = read_bloques_by_entrenamiento(entrenamiento_id=bloque.fkEntrenamiento, db=db, current_user=current_user)
        new_posicion = len(total_bloques) + 1
    if(new_posicion > bloque.fldNOrden):
        bloques = db.query(tbl_bloques).filter(tbl_bloques.fkEntrenamiento == bloque.fkEntrenamiento).filter(tbl_bloques.fldNOrden > bloque.fldNOrden).filter(tbl_bloques.fldNOrden <= new_posicion).all()
        for b in bloques:
            b.fldNOrden = b.fldNOrden - 1
        bloque.fldNOrden = new_posicion
    else:
        bloques = db.query(tbl_bloques).filter(tbl_bloques.fkEntrenamiento == bloque.fkEntrenamiento).filter(
            tbl_bloques.fldNOrden < bloque.fldNOrden).filter(tbl_bloques.fldNOrden >= new_posicion).all()
        for b in bloques:
            b.fldNOrden = b.fldNOrden + 1
        bloque.fldNOrden = new_posicion
    db.commit()
    db.refresh(bloque)
    return bloque


def clonar(
    old_entrenamiento: int,
    new_entrenamiento: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    bloques = db.query(tbl_bloques).filter(tbl_bloques.fkEntrenamiento == old_entrenamiento).all()
    for obj in bloques:
        new = tbl_bloques(fldSDescripcion=obj.fldSDescripcion,
                        fkEntrenamiento=new_entrenamiento,
                        fldNDescanso=obj.fldNDescanso,
                        fldNOrden=obj.fldNOrden,
                        fkCreador=obj.fkCreador,
                        fkPadre=obj.id)
        db.add(new)
        db.commit()
        db.refresh(new)
        series.clonar(old_bloque=obj.id, new_bloque=new.id, db=db)
    return


























