from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_plan, tbl_model
from app.models.tbl_ejercicio import tbl_ejercicio
from app.models.tbl_plan import tbl_planes
from app.schemas import PlanCreate, EjercicioCreate, Umbral, PlanResumen, EjercicioResumen

router = APIRouter()


@router.get("/", response_model=List[schemas.PlanResumen])
def read_plans(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    rol = current_user.fkRol
    plan: List[tbl_plan] = crud.plan.get_multi_by_rol(db, user=current_user.id, rol=rol, skip=skip, limit=limit)
    return plan


@router.get("/user", response_model=List[List[schemas.PlanResumen]])
def read_plans_user(
        db: Session = Depends(deps.get_db),
        user: int = 0,
        listado: int = 0,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    rol = current_user.fkRol
    resultado = []
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0, )

    # Pasados
    res = []
    if listado == 2 or listado == 3 or listado == 6 or listado == 7:
        sql_text = text("""
                        select tp.id , 
                            (select (count(*)/sum(te2.fldNRepeticiones)) from tbl_historico_valores thv left join tbl_umbrales tu on (thv.fkUmbral = tu.id) left join tbl_ejercicio te2 on (te2.id = tu.fkEjercicio) where te2.fkPlan = tp.id and thv.fldFvalor >= tu.fldFValor) as accurate
                        from  tbl_planes tp
                        left join tbl_asignado ta on (ta.fkPlan = tp.id)
                        where ta.fkUsuario = """ + str(user) + """ and (Select max(te.fldDDia)
                            from tbl_ejercicio te 
                            WHERE te.fkPlan = tp.id) < '""" + str(today) + """';
                    """)
        print(sql_text)
        res = db.execute(sql_text)
    resultado.append(completar(db=db, res=res))

    # Actuales
    res = []
    if listado >= 4:
        sql_text = text("""
                        select tp.id , 
                            (select (count(*)/sum(te2.fldNRepeticiones)) from tbl_historico_valores thv left join tbl_umbrales tu on (thv.fkUmbral = tu.id) left join tbl_ejercicio te2 on (te2.id = tu.fkEjercicio) where te2.fkPlan = tp.id and thv.fldFvalor >= tu.fldFValor) as accurate
                        from  tbl_planes tp
                        left join tbl_asignado ta on (ta.fkPlan = tp.id)
                        where ta.fkUsuario = """ + str(user) + """ and (Select max(te.fldDDia)
                            from tbl_ejercicio te 
                            WHERE te.fkPlan = tp.id) >= '""" + str(today) + """'
                           and (Select min(te.fldDDia)
                            from tbl_ejercicio te 
                            WHERE te.fkPlan = tp.id) <= '""" + str(today) + """';
                    """)
        res = db.execute(sql_text)
    resultado.append(completar(db=db, res=res))

    # Futuros
    res = []
    if listado == 1 or listado == 3 or listado == 5 or listado == 7:
        sql_text = text("""
                            select tp.id , 
                                (select (count(*)/sum(te2.fldNRepeticiones)) from tbl_historico_valores thv left join tbl_umbrales tu on (thv.fkUmbral = tu.id) left join tbl_ejercicio te2 on (te2.id = tu.fkEjercicio) where te2.fkPlan = tp.id and thv.fldFvalor >= tu.fldFValor) as accurate
                            from  tbl_planes tp
                            left join tbl_asignado ta on (ta.fkPlan = tp.id)
                            where ta.fkUsuario = """ + str(user) + """ and not((Select min(te.fldDDia)
                                from tbl_ejercicio te 
                                WHERE te.fkPlan = tp.id) <= '""" + str(today) + """');
                        """)
        res = db.execute(sql_text)
    resultado.append(completar(db=db, res=res))
    return resultado


def completar(db: Session, res: Any) -> List[schemas.PlanResumen]:
    resultado = []
    for row in res:
        plan = crud.plan.get(db=db, id=row[0])
        obj = PlanResumen()
        obj.fldSNombre = plan.fldSNombre
        obj.id = plan.id
        if(row[1]):
            obj.adherencia = row[1]*100
        else:
            obj.adherencia = 0
        obj.ejercicios = []
        for ejercicio in plan.ejercicios:
            modelo = db.query(tbl_model).filter(tbl_model.id == ejercicio.fkEjercicio).first()
            aux = EjercicioResumen()
            aux.id = ejercicio.id
            aux.fkEjercicio = modelo.id
            aux.fldNRepeticiones = ejercicio.fldNRepeticiones
            aux.fldDDia = ejercicio.fldDDia
            aux.imagen = modelo.fldSImage
            aux.nombre = modelo.fldSName
            if len(ejercicio.umbrales) > 0:
                aux.fkUmbral = ejercicio.umbrales[0].id
                aux.umbral = ejercicio.umbrales[0].fldFValor
            else:
                aux.umbral = 50
            obj.ejercicios.append(aux)
        resultado.append(obj)
    return resultado


@router.post("/", response_model=schemas.Plan)
def create_plan(
        *,
        db: Session = Depends(deps.get_db),
        plan_in: schemas.PlanCreate,
        user: Optional[int] = None,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new model.
    """
    if not plan_in.fkCreador:
        plan_in.fkCreador = current_user.id
    if current_user.fkRol > 1:
        plan = crud.plan.create_with_owner(db=db, obj_in=plan_in)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    if plan.fldBGenerico is not None:
        asignar = schemas.AsignadoCreate(fkUsuario=user, fkPlan=plan.id, fldDTimeAsignacion=datetime.today())
        crud.asignado.create_with_validation(db=db, obj_in=asignar, user=current_user)
        ejercicios: List[tbl_ejercicio] = crud.ejercicio.get_multi_by_rol(db=db, user=current_user.id, rol=current_user.fkRol,
                                                                          id=plan_in.fldBGenerico)
        for ejercicio in ejercicios:
            umbrales = [Umbral(fldFValor=ejercicio.umbrales[0].fldFValor, fkTipo=1)]
            add = EjercicioCreate(fkEjercicio=ejercicio.fkEjercicio, umbrales=umbrales, fldNRepeticiones=ejercicio.fldNRepeticiones)
            crud.ejercicio.create_with_owner(db=db, db_obj=plan, obj_in=add)
    return plan


@router.put("/{id}", response_model=schemas.Plan)
def update_plan(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        plan_in: schemas.PlanUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an model.
    """
    plan = read_plan(db=db, id=id, current_user=current_user)  # Check model exists
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        plan = crud.plan.update(db=db, db_obj=plan, obj_in=plan_in)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return plan


@router.get("/{id}", response_model=schemas.Plan)
def read_plan(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    plan = crud.plan.get(db=db, id=id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return plan


@router.post("/addDia", response_model=schemas.Plan)
def addDia(
        *,
        db: Session = Depends(deps.get_db),
        planId: int,
        dia: str,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    dia += " 00:00:00"
    diaDT = datetime.strptime(dia, "%d/%m/%y %H:%M:%S")
    plan = crud.plan.get(db=db, id=planId)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    for ejercicio in plan.ejercicios:
        if ejercicio.fldDDia is None:
            umbrales = [Umbral(fldFValor=ejercicio.umbrales[0].fldFValor, fkTipo=1)]
            add = EjercicioCreate(fkEjercicio=ejercicio.fkEjercicio, umbrales=umbrales, fldNRepeticiones=ejercicio.fldNRepeticiones, fldDDia=diaDT)
            crud.ejercicio.create_with_owner(db=db, db_obj=plan, obj_in=add)
    return


@router.delete("/{id}", response_model=schemas.Plan)
def delete_plan(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an model.
    """
    read_plan(db=db, id=id, current_user=current_user)  # Check model exists
    plan = crud.plan.get(db=db, id=id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if check_permission(db=db, user=current_user.id, plan=plan, rol=current_user.fkRol):
        model = crud.plan.remove(db=db, id=id)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return model


def check_permission(
        *,
        db: Session,
        user: int,
        plan: tbl_planes,
        rol: int,
) -> Any:
    if rol == 1:
        res = crud.asignado.count(db=db, user=user, plan=plan.id) > 1
    else:
        if rol == 2:
            res = (user == plan.fkCreador)
        else:
            if rol == 3:
                res = crud.asignado.count(db=db, user=user, plan=plan.id) > 1
                res = res or (user == plan.fkCreador)
            else:
                res = True

    return res
