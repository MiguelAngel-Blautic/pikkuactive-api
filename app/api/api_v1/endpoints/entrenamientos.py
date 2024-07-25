from datetime import date, datetime
from statistics import mean
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import planes, bloques
from app.api.api_v1.endpoints.bloques import read_bloques_by_id, read_valores_bloques, read_bloques_by_id_detalle
from app.api.api_v1.endpoints.ejercicios import read_ejercicios_by_id
from app.api.api_v1.endpoints.series import read_series_by_id
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_entrenamientos, tbl_bloques, tbl_series, tbl_ejercicios, \
    tbl_dato_adicional_plan
from app.schemas import ResumenEstadistico
from app.schemas.ejercicio import Resultado, EjercicioDetalles

router = APIRouter()


@router.get("/", response_model=List[schemas.Entrenamiento])
def read_entrenamientos(
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    if current_user.fkRol == 1:
        entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkCreador == current_user.id).filter(tbl_entrenamientos.fkPlan == None).all()
        return entrenamientos
    else:
        planes = db.query(tbl_planes).filter(tbl_planes.fkCliente == current_user.id).all()
        entrenamientos = db.query(tbl_entrenamientos).filter(
            tbl_entrenamientos.fkPlan.in_([p.id for p in planes])).all()
        return entrenamientos


@router.post("/list", response_model=List[schemas.ResumenEstadistico])
def read_entrenamientos_by_id_plan(
        plan: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sql = text("""
        SELECT ten.fkPadre, ten2.fldSNombre, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia) as lastDay
from tbl_ejercicios te
    join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento) join tbl_entrenamientos ten2 on (ten2.id = ten.fkPadre)
   WHERE ten.fldDDia is not null and ten.fkPlan = """+str(plan)+""" group by ten.fkPadre order by lastDay desc; """)
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
            join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
            where ten.fkPadre=""" + str(row[0]) + """ and tre.fkTipoDato = 2;""")
        total = db.execute(sql)
        for t in total:
            adherencia = (t[0] * 100) / row[2]
        entrada = ResumenEstadistico(
            tipo=2,
            nombre=row[1],
            adherencia=adherencia,
            completo=min(completado, 100),
            id=row[0],
        )
        response.append(entrada)
    return response


def read_valores_entrenamiento(
    *,
    db: Session = Depends(deps.get_db),
    plan: int,
) -> Any:
    res = []
    entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkPadre is None).filter(tbl_entrenamientos.fkPlan == plan).all()
    for e in entrenamientos:
        subentrenes = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkPadre == e.id).all()
        for s in subentrenes:
            bloques = read_valores_bloques(db=db, entrene=s.id)
            adh = sum(b.adherencia for b in bloques) / len(bloques)
            res.append(Resultado(id=s.id, nombre=s.fldSNombre, adherencia=adh, completo=100))
    return res


@router.get("/detail/calendar/")
def read_entrenamientos_by_id_detalle(
        id: int,
        dia: datetime,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = []
    entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkPlan == id).filter(tbl_entrenamientos.fldDDia == dia).all()
    for entrenamiento in entrenamientos:
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The entrenamiento doesn't exist")
        adherencias = []
        bloques = read_bloques_by_id_detalle(entrenamiento.id, db)
        for bloque in bloques:
            adherencias.append(bloque.adherencia)
        res.append(EjercicioDetalles(
            fldNOrden=0,
            fldNDescanso=0,
            fldNRepeticiones=0,
            fldNDuracion=0,
            fldNDuracionEfectiva=0,
            fldFVelocidad=0,
            fkModelo=0,
            fldSToken="",
            id=entrenamiento.id,
            adherencia=round(mean(adherencias)),
            items=bloques,
            tipo=2
        ))
    return res


@router.get("/detail/{id}", response_model=schemas.EntrenamientoCompleto)
def read_entrenamiento_detail(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    entrenamiento = read_entrenamiento_by_id(db=db, id=id, current_user=current_user)
    bloques = db.query(tbl_bloques).filter(tbl_bloques.fkEntrenamiento == entrenamiento.id).all()
    listaBloques = []
    for bloque in bloques:
        series = db.query(tbl_series).filter(tbl_series.fkBloque == bloque.id).all()
        listaSeries = []
        for serie in series:
            ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == serie.id).all()
            listaEjercicios = []
            for ejercicio in ejercicios:
                ej = read_ejercicios_by_id(id=ejercicio.id, db=db, current_user=current_user)
                listaEjercicios.append(ej)
            ser = read_series_by_id(id=serie.id, db=db, current_user=current_user)
            ser.ejercicios = listaEjercicios
            listaSeries.append(ser)
        bloq = read_bloques_by_id(id=bloque.id, db=db, current_user=current_user)
        bloq.series = listaSeries
        listaBloques.append(bloq)
    entrenamiento.bloques = listaBloques
    listaSensores = []
    sensoresAdicionales = db.query(tbl_dato_adicional_plan).filter(tbl_dato_adicional_plan.fkEntrenamiento == entrenamiento.id).all()
    for adicional in sensoresAdicionales:
        listaSensores.append([adicional.fldNPosicion, adicional.fldNTipoDato])
    entrenamiento.dispositivos = listaSensores
    return entrenamiento



@router.get("/dia", response_model=List[schemas.Entrenamiento])
def read_entrenamientos_by_dia(
    dia: date,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    if current_user.fkRol == 1:
        entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fldDDia == dia).filter(
            tbl_entrenamientos.fkCreador == current_user.id).all()
        return entrenamientos
    else:
        planes = db.query(tbl_planes).filter(tbl_planes.fkCliente == current_user.id).all()
        entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fldDDia == dia).filter(
            tbl_entrenamientos.fkPlan.in_([p.id for p in planes])).all()
        return entrenamientos


@router.get("/plan", response_model=List[schemas.Entrenamiento])
def read_entrenamientos_by_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    entrenamientos = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkCreador == current_user.id).filter(tbl_entrenamientos.fkPlan == plan_id).filter(tbl_entrenamientos.fldDDia == None).all()
    return entrenamientos


@router.get("/{id}", response_model=schemas.Entrenamiento)
def read_entrenamiento_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    entrenamiento = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.id == id).first()
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The id doesn't exist")
    if current_user.fkRol == 1:
        if entrenamiento.fkCreador != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    else:
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return entrenamiento



@router.post("/", response_model=schemas.Entrenamiento)
def create_entrenamiento(
    *,
    db: Session = Depends(deps.get_db),
    entrenamiento_in: schemas.EntrenamientoCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    newEntrenamiento = tbl_entrenamientos(fldSNombre=entrenamiento_in.fldSNombre,
                        fkCreador=current_user.id)
    db.add(newEntrenamiento)
    db.commit()
    db.refresh(newEntrenamiento)
    for adicional in entrenamiento_in.dispositivos:
        dato = tbl_dato_adicional_plan(
            fldNPosicion=adicional[0],
            fldNTipoDato=adicional[1],
            fkEntrenamiento=newEntrenamiento.id
        )
        db.add(dato)
        db.commit()
    return newEntrenamiento


@router.post("/plan", response_model=schemas.Entrenamiento)
def asignar_entrenamiento_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    entrenamiento_id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Asignar un entrenamiento generico a un plan
    """
    plan = planes.read_planes_by_id(db=db, current_user=current_user, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=entrenamiento_id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    newEntrenamiento = tbl_entrenamientos(fldSNombre=entrenamiento.fldSNombre,
                                          fkCreador=current_user.id,
                                          fkPadre=entrenamiento.id,
                                          fkPlan=plan.id)
    db.add(newEntrenamiento)
    db.commit()
    db.refresh(newEntrenamiento)
    adicionales = db.query(tbl_dato_adicional_plan).filter(
        tbl_dato_adicional_plan.fkEntrenamiento == entrenamiento.id).all()
    for adicional in adicionales:
        dato = tbl_dato_adicional_plan(
            fldNPosicion=adicional.fldNPosicion,
            fldNTipoDato=adicional.fldNPosicion,
            fkEntrenamiento=newEntrenamiento.id
        )
        db.add(dato)
        db.commit()
    bloques.clonar(old_entrenamiento=entrenamiento.id, new_entrenamiento=newEntrenamiento.id, db=db)
    return newEntrenamiento


@router.post("/sesion", response_model=schemas.Entrenamiento)
def asignar_entrenamiento_sesion(
    *,
    db: Session = Depends(deps.get_db),
    dia: date,
    entrenamiento_id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Asignar un entrenamiento de un plan a una fecha
    """
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=entrenamiento_id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    plan = planes.read_planes_by_id(db=db, current_user=current_user, id=entrenamiento.fkPlan)
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    # entrenamientoAct = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkPlan == plan.id).filter(
    #     tbl_entrenamientos.fldDDia == dia).all()
    # if len(entrenamientoAct) > 0:
    #     raise HTTPException(status_code=404, detail="The training already exist")
    newEntrenamiento = tbl_entrenamientos(fldSNombre=entrenamiento.fldSNombre,
                                          fkCreador=current_user.id,
                                          fkPadre=entrenamiento.id,
                                          fkPlan=plan.id,
                                          fldDDia=dia)
    db.add(newEntrenamiento)
    db.commit()
    db.refresh(newEntrenamiento)
    adicionales = db.query(tbl_dato_adicional_plan).filter(tbl_dato_adicional_plan.fkEntrenamiento == entrenamiento.id).all()
    for adicional in adicionales:
        dato = tbl_dato_adicional_plan(
            fldNPosicion = adicional.fldNPosicion,
            fldNTipoDato = adicional.fldNPosicion,
            fkEntrenamiento = newEntrenamiento.id
        )
        db.add(dato)
        db.commit()
    bloques.clonar(old_entrenamiento=entrenamiento.id, new_entrenamiento=newEntrenamiento.id, db=db)
    return newEntrenamiento


@router.put("/{id}", response_model=schemas.Plan)
def update_entrenamiento(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    entrenamiento_in: schemas.EntrenamientoUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    entrenamiento.fldSNombre = entrenamiento_in.fldSNombre
    entrenamiento.fldDDia = entrenamiento_in.fldDDia
    db.commit()
    db.refresh(entrenamiento)
    adicionales = db.query(tbl_dato_adicional_plan).filter(
        tbl_dato_adicional_plan.fkEntrenamiento == entrenamiento.id).all()
    for adicional in adicionales:
        db.delete(adicional)
        db.commit()
    for adicional in entrenamiento_in.dispositivos:
        dato = tbl_dato_adicional_plan(
            fldNPosicion=adicional[0],
            fldNTipoDato=adicional[1],
            fkEntrenamiento=entrenamiento.id
        )
        db.add(dato)
        db.commit()
    return entrenamiento


@router.delete("/{id}")
def delete_entrenamiento(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    entrenamiento = read_entrenamiento_by_id(db=db, current_user=current_user, id=id)
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="The training doesn't exist")
    db.delete(entrenamiento)
    db.commit()
    return
