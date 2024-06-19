from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.users import read_user_by_id_plataforma
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes
from app.schemas import ResumenEstadistico

router = APIRouter()

@router.get("/platform/", response_model=List[schemas.Plan])
def read_planes_by_user_plataforma(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    user = read_user_by_id_plataforma(user_id=user_id, db=db, current_user=current_user)
    return read_planes_by_user(user_id=user.id, db=db, current_user=current_user)


@router.post("/list", response_model=List[schemas.ResumenEstadistico])
def read_planes_by_id_user(
        user: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = [None]
    sql = text("""
        SELECT tp.id, tp.fldSNombre, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia) as lastDay
    from tbl_ejercicios te
    join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
    join tbl_planes tp on (tp.id = ten.fkPlan) where ten.fldDDia is not null and tp.fkCliente = """ + str(
        user_id) + """ group by tp.id, tp.fldSNombre order by lastDay desc; """)
    res = db.execute(sql)
    adherencia = 0
    actual = datetime.now()
    for row in res:
        diaAct = actual.date() - row[3]
        dias = row[4] - row[3]
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
        entrada = ResumenEstadistico(
            tipo=1,
            nombre=row[1],
            adherencia=adherencia,
            completo=min(completado, 100),
            id=row[0],
        )
        response.append(entrada)
        if response[0] is None:
            response[0] = entrada
        if row[3] <= actual.date() <= row[4]:
            response[0] = entrada
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
