from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
import numpy as np
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.users import read_user_by_id_plataforma
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes
from app.schemas import ResumenEstadistico, EntrenamientoDetalle, PlanDetalle, EjercicioDetalle

router = APIRouter()

@router.get("/platform/", response_model=List[schemas.Plan])
def read_planes_by_user_plataforma(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    user = read_user_by_id_plataforma(user_id=user_id, db=db, current_user=current_user)
    return read_planes_by_user(user_id=user.id, db=db, current_user=current_user)


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
    return response


@router.get("/", response_model=List[schemas.Plan])
def read_planes_by_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    planes = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.fkCliente == user_id).all()
    return planes


@router.get("/{id}", response_model=schemas.Plan)
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
    plan = db.query(tbl_planes).filter(tbl_planes.fkCreador == current_user.id).filter(tbl_planes.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="The plan doesn't exist")

    # CALCULO DE LOS ENTRENAMIENTOS
    entrenamientos = []
    adherenciaTot = 0
    progresoTot = 0
    sql = text("""
            SELECT ten.fkPadre, ten2.fldSNombre, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia) as lastDay
    from tbl_ejercicios te
        join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento) join tbl_entrenamientos ten2 on (ten2.id = ten.fkPadre)
       WHERE ten.fldDDia is not null and ten.fkPlan = """ + str(
        plan.id) + """ group by ten.fkPadre order by lastDay desc; """)
    res = db.execute(sql)
    adherencia = 0
    actual = datetime.now()
    numTotal = 0
    for row in res:
        numTotal += 1
        diaAct = actual.date() - row[3]
        dias = row[4] - row[3]
        if dias.days <= 0:
            completado = 0
        else:
            completado = (100 * diaAct.days) / dias.days
        completado = min(completado, 100.0)
        sql = text("""
            SELECT count(*)
                from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
                join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                where ten.fkPadre=""" + str(row[0]) + """ and tre.fkTipoDato = 2;""")
        total = db.execute(sql)
        for t in total:
            if completado == 0:
                adherencia = 0
            else:
                adherencia = (((t[0] * 100) / float(row[2]))/completado)*100
        sql = text("""
            SELECT distinct ten.fldDDia
            from tbl_entrenamientos ten
            WHERE ten.fldDDia is not null and ten.fkPadre = """ + str(row[0]) +""" order by ten.fldDDia desc""")
        diasList = []
        dias = db.execute(sql)
        for d in dias:
            diasList.append(d[0])
        entrada = EntrenamientoDetalle(
            nombre=row[1],
            adherencia=adherencia,
            progreso=completado,
            id=row[0],
            fechas=diasList
        )
        adherenciaTot += adherencia
        progresoTot += completado
        entrenamientos.append(entrada)
    if numTotal > 0:
        progresoTot /= numTotal
        adherenciaTot /= numTotal
    else:
        progresoTot = 0
        adherenciaTot = 0

    # CALCULO DE LOS EJERCICIOS
    ejercicios = []
    sql = text("""
            SELECT te.fkModelo, te.fldSToken, sum(te.fldNRepeticioneS * ts.fldNRepeticiones)
    from tbl_ejercicios te
        join tbl_ejercicios te2 on (te2.id = te.fkPadre)
        join tbl_series ts on (ts.id = te2.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
       WHERE ten.fkPlan = """ + str(plan.id) + """ group by te.fkModelo, te.fldSToken; """)
    res = db.execute(sql)
    adherencia = 0
    for row in res:
        if row[0] != None:
            sql = text("""
                SELECT count(*)
                    from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) 
                    join tbl_ejercicios te on (te.id = tre.fkEjercicio) join tbl_series ts on (ts.id = te.fkSerie)
                    join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                    where te.fkModelo=""" + str(row[0]) + """ and ten.fkPlan=""" + str(plan.id) + """ and tre.fkTipoDato = 2;""")
            total = db.execute(sql)
            for t in total:
                adherencia = (t[0] * 100) / row[2]
            entrada = EjercicioDetalle(
                nombre=row[1],
                adherencia=(float(adherencia))/progresoTot,
                id=row[0],
            )
            ejercicios.append(entrada)
    listaDias = [d for ent in entrenamientos for d in ent.fechas]
    if len(listaDias) < 1:
        inicio = None
        fin = None
    else:
        inicio = min(listaDias)
        fin = max(listaDias)
    return PlanDetalle(
        nombre = plan.fldSNombre,
        id = plan.id,
        inicio = inicio,
        fin = fin,
        adherencia = adherenciaTot,
        progreso = progresoTot,
        entrenamientos = entrenamientos,
        ejercicios = ejercicios)


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
    user = read_user_by_id_plataforma(user_id=plan_in.fkCliente, db=db, current_user=current_user)
    plan_in.fkCliente = user.id
    return create_plan(db=db, plan_in=plan_in, current_user=current_user)


@router.post("/", response_model=schemas.Plan)
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
    return
