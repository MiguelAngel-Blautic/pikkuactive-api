from datetime import datetime
from statistics import mean
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
import numpy as np
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.entrenamientos import read_entrenamientos_by_id_detalle
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_entrenamientos, tbl_ejercicios, tbl_series, tbl_bloques
from app.schemas import ResumenEstadistico, EntrenamientoDetalle, PlanDetalle, EjercicioDetalle, UserDetails
from app.schemas.ejercicio import EjercicioDetalles

router = APIRouter()


def read_user_by_id_plataforma(
        user_id: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(tbl_user).filter(tbl_user.idPlataforma == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="The user doesn't exist")
    sql = text("""
        SELECT tp.id, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia)
    from tbl_ejercicios te
    join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
    join tbl_planes tp on (tp.id = ten.fkPlan) where ten.fldDDia is not null and tp.fkCliente = """ + str(
        user.id) + """ group by tp.id; """)
    res = db.execute(sql)
    adherencia = []
    completado = []
    actual = datetime.now()
    for row in res:
        if row[2] <= actual.date() <= row[3]:
            diaAct = actual.date() - row[2]
            dias = row[3] - row[2]
            if dias.days > 0:
                completado.append((100 * diaAct.days) / dias.days)
            else:
                completado.append((100 * diaAct.days))
            sql = text("""
            SELECT count(*)
                from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
                join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                join tbl_planes tp on (tp.id = ten.fkPlan) where tp.id=""" + str(
                row[0]) + """ and tre.fkTipoDato = 2; """)
            total = db.execute(sql)
            for t in total:
                adherencia.append((t[0] * 100) / row[1])
    return UserDetails(fldSEmail=user.fldSEmail,
                       id=user.id,
                       fkRol=user.fkRol,
                       idPlataforma=user.idPlataforma,
                       fldSDireccion=user.fldSDireccion,
                       fldSTelefono=user.fldSTelefono,
                       fldSImagen=user.fldSImagen,
                       fldSFullName=user.fldSFullName,
                       adherencia=np.mean(adherencia),
                       completado=np.mean(completado))


@router.get("/platform/", response_model=List[schemas.Plan])
def read_planes_by_user_plataforma(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    user = read_user_by_id_plataforma(user_id=user_id, db=db, current_user=current_user)
    res = read_planes_by_user(user_id=user.id, db=db, current_user=current_user)
    db.close()
    return res


@router.get("/dias")
def read_planes_by_dia(
        year: int,
        month: int,
        user: Optional[int] = None,
        plan: Optional[int] = None,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    result = []
    if plan:
        sql = text("""
            select distinct day(te.fldDDia)
            from tbl_entrenamientos te
            where te.fkPlan = """+str(plan)+""" and te.fldDDia is not null and year(te.fldDDia) = """+str(year)+""" and MONTH(te.fldDDia) = """+str(month)+""";
        """)
    else:
        sql = text("""
            select distinct day(te.fldDDia)
            from tbl_entrenamientos te join tbl_planes tp on (tp.id = te.fkPlan)
            where tp.fkCliente = """ + str(user) + """ and te.fldDDia is not null and year(te.fldDDia) = """ + str(year) + """ and MONTH(te.fldDDia) = """ + str(month) + """;
        """)
    res = db.execute(sql)
    for row in res:
        result.append(row[0])
    db.close()
    return result

@router.post("/list", response_model=List[schemas.ResumenEstadistico])
def read_planes_by_id_user(
        user: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    planes = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.fkCliente == user).all()
    """
    Get a specific user by id.
    """
    adherencias = []
    completos = []
    response = [None]
    for p in planes:
        sql = text("""
            SELECT tp.id, tp.fldSNombre, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia) as lastDay
        from tbl_ejercicios te
        join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
        join tbl_planes tp on (tp.id = ten.fkPlan) where ten.fldDDia is not null and tp.id = """ + str(
            p.id) + """ group by tp.id, tp.fldSNombre order by lastDay desc; """)
        res = db.execute(sql)
        adherencia = 0
        actual = datetime.now()
        entrada = ResumenEstadistico(
            tipo=1,
            nombre=p.fldSNombre,
            adherencia=0,
            completo=0,
            id=p.id,
        )
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
                join tbl_planes tp on (tp.id = ten.fkPlan) where tp.id=""" + str(
                row[0]) + """ and tre.fkTipoDato = 2; """)
            total = db.execute(sql)
            for t in total:
                adherencia = (t[0] * 100) / row[2]
            entrada.adherencia = adherencia
            entrada.completo = min(completado, 100)
            if row[3] <= actual.date() <= row[4]:
                adherencias.append(entrada.adherencia)
                completos.append(entrada.completo)
        response.append(entrada)
    if adherencias != []:
        adherencia = np.mean(adherencias)
    else:
        adherencia = 0
    if completos != []:
        completo = np.mean(completos)
    else:
        completo = 0
    response[0] = ResumenEstadistico(
            tipo=1,
            nombre="Planes actuales",
            adherencia=round(adherencia),
            completo=round(completo),
            id=0,
        )
    db.close()
    return response


@router.get("/", response_model=List[schemas.Plan])
def read_planes_by_user_server(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_planes_by_user(user_id, db, current_user)
    db.close()
    return res


def read_planes_by_user(
        user_id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    planes = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.fkCliente == user_id).all()
    return planes


@router.get("/detail/user/")
def read_planes_by_id_detalle_user_server(
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_planes_by_id_detalle_user(id, db, current_user)
    db.close()
    return res


def read_planes_by_id_detalle_user(
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    return read_planes_by_id_calendar_detail(id, None, db, current_user)


@router.get("/detail/calendar/")
def read_planes_by_id_detalle(
        id: int,
        date: datetime,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_planes_by_id_calendar_detail(id, date, db, current_user)
    db.close()
    return res

def read_planes_by_id_calendar_detail(
        id: int,
        date: Optional[datetime] = None,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = []
    planes = db.query(tbl_planes).filter(tbl_planes.fkCliente == id).all()
    for plan in planes:
        if not plan:
            raise HTTPException(status_code=404, detail="The plan doesn't exist")
        adherencias = []
        completos = []
        entrenamientos = read_entrenamientos_by_id_detalle(plan.id, date, db, current_user)
        for entrenamiento in entrenamientos:
            adherencias.append(entrenamiento.adherencia)
            completos.append(entrenamiento.completo)
        if len(adherencias) < 1:
            adherencias = [0]
        if len(completos) < 1:
            completos = [0]
        completo = mean(completos)
        adherencia = mean(adherencias)
        if completo > 0:
            adherencia /= completo
            for ent in entrenamientos:
                ent.adherencia /= completo
                for bloq in ent.items:
                    bloq.adherencia /= completo
                    for ser in bloq.items:
                        ser.adherencia /= completo
                        for ejer in ser.items:
                            ejer.adherencia /= completo
        res.append(EjercicioDetalles(
            fldNOrden=0,
            fldNDescanso=0,
            fldNRepeticiones=0,
            fldNDuracion=0,
            fldNDuracionEfectiva=0,
            fldFVelocidad=0,
            fkModelo=0,
            fldSToken="",
            id=plan.id,
            adherencia=adherencia,
            items=entrenamientos,
            tipo=1,
            completo=completo,
            duracion = 0,
            nombre=plan.fldSNombre
        ))
    return res


@router.get("/{id}", response_model=schemas.Plan)
def read_planes_by_id_server(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_planes_by_id(id, db, current_user)
    db.close()
    return res


def read_planes_by_id(
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    plan = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    return plan


@router.get("/detalles/{id}", response_model=schemas.PlanDetalle)
def read_planes_detalles_by_id(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    completosTot = []
    adherenciaTot = []
    plan = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")

    listaDias = []
    entrenamientos = []
    entrenamientosDb = db.query(tbl_entrenamientos).filter(tbl_entrenamientos.fkPlan == id).filter(
        tbl_entrenamientos.fldDDia == None).all()
    results = read_entrenamientos_by_id_detalle(id, None, db, current_user)
    for entDb in entrenamientosDb:
        resultsFilter = [r for r in results if r.id == entDb.id]
        adherencias = [r.adherencia for r in resultsFilter]
        completos = [r.completo for r in resultsFilter]
        if len(adherencias) < 1:
            adherencias = [0]
        if len(completos) < 1:
            completos = [0]
        dias = db.query(tbl_entrenamientos.fldDDia).filter(tbl_entrenamientos.fkPadre == entDb.id).distinct()
        dias = [d.fldDDia for d in dias]
        listaDias = listaDias + dias
        if mean(completos) > 0:
            adh1 = mean(adherencias) / mean(completos)
        else:
            adh1 = 0
        entrenamientos.append(EntrenamientoDetalle(
            nombre=entDb.fldSNombre,
            adherencia=adh1,
            progreso=mean(completos),
            id=entDb.id,
            fechas=dias
        ))
        if 0 < mean(completos) < 1:
            completosTot.append(mean(completos))
            adherenciaTot.append(mean(adherencias))
    ejercicios = []
    ejerciciosDb = (db.query(tbl_ejercicios.fkModelo, tbl_ejercicios.fldSToken).join(tbl_series, tbl_ejercicios.fkSerie == tbl_series.id).
                    join(tbl_bloques, tbl_series.fkBloque == tbl_bloques.id).
                    join(tbl_entrenamientos, tbl_bloques.fkEntrenamiento == tbl_entrenamientos.id).
                    filter(tbl_entrenamientos.fkPlan == id).distinct())
    for ejDb in ejerciciosDb:
        ejercicios.append(EjercicioDetalle(
                 nombre=ejDb.fldSToken,
                 adherencia=0,
                 id=ejDb.fkModelo,
             ))
    if len(listaDias) < 1:
        inicio = None
        fin = None
    else:
        inicio = min(listaDias)
        fin = max(listaDias)
    if len(completosTot) < 1:
        completosTot = [0]
        adherenciaTot = [0]
    if mean(completosTot) > 0:
        adh = mean(adherenciaTot) / mean(completosTot)
    else:
        adh = 0
    res = PlanDetalle(
        nombre = plan.fldSNombre,
        id = plan.id,
        inicio = inicio,
        fin = fin,
        adherencia = adh,
        progreso = mean(completosTot),
        entrenamientos = entrenamientos,
        ejercicios = ejercicios)
    db.close()
    return res


@router.post("/platform/", response_model=schemas.Plan)
def create_plan_plataforma(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    user = db.query(tbl_user).filter(tbl_user.idPlataforma == plan_in.fkCliente).first()
    plan_in.fkCliente = user.id
    res = create_plan(db=db, plan_in=plan_in, current_user=current_user)
    db.close()
    return res


@router.post("/", response_model=schemas.Plan)
def create_plan_server(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = create_plan(db=db, plan_in=plan_in, current_user=current_user)
    db.close()
    return res


def create_plan(
        *,
        db: Session = Depends(deps.get_db),
        plan_in: schemas.PlanCreate,
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    newPlan = tbl_planes(fldSNombre=plan_in.fldSNombre,
                        fkCreador=current_user.id,
                        fkCliente=plan_in.fkCliente)
    db.add(newPlan)
    db.commit()
    db.refresh(newPlan)
    return newPlan


@router.put("/{id}", response_model=schemas.Plan)
def update_plan(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    plan = read_planes_by_id(id=id, db=db, current_user=current_user)
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")
    plan.fldSNombre = plan_in.fldSNombre
    db.commit()
    db.refresh(plan)
    db.close()
    return plan


@router.delete("/{id}")
def delete_plan(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    plan = read_planes_by_id(id=id, db=db, current_user=current_user)
    db.delete(plan)
    db.commit()
    db.close()
    return
