from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints.ejercicio import read_ejercicio
from app.api.api_v1.endpoints.umbral import read_umbral
from app.models import tbl_sesion, tbl_user
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.api.api_v1.endpoints.sesion import read_plan, check_permission
from app.schemas import AsignadoCreate

router = APIRouter()


@router.post("/entrenar", response_model=int)
def updatete_entrenar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    entrena = crud.entrena.get(db=db, id=id)
    if not entrena:
        raise HTTPException(status_code=404, detail="Relation not found")
    entrena = crud.entrena.remove(db=db, id=id)
    entrena_in = schemas.EntrenaCreate(fkProfesional=entrena.fkProfesional, fkUsuario=entrena.fkUsuario)
    res = crud.entrena.create_with_owner(db=db, obj_in=entrena_in, user=current_user)
    if res:
        if res.fldBConfirmed:
            return 2
        else:
            return 1
    else:
        return 0


@router.put("/entrenar", response_model=int)
def add_entrenar(
        *,
        db: Session = Depends(deps.get_db),
        profesional: int,
        usuario: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    entrena_in = schemas.EntrenaCreate(fkProfesional=profesional, fkUsuario=usuario)
    resultado = crud.entrena.create_with_owner(db=db, obj_in=entrena_in, user=current_user)
    if resultado:
        if current_user.fkRol >= 1:
            return 2
        else:
            return 1
    else:
        return 0


@router.post("/aceptar", response_model=int)
def aceptar(
        *,
        db: Session = Depends(deps.get_db),
        profesional: int,
        usuario: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    sql_text = text("""
            update tbl_entrena set fldBConfirmed = 2 where fkProfesional = """ + str(profesional) + """ and fkUsuario = """ + str(usuario))
    db.execute(sql_text)
    if db.commit():
        return 1
    else:
        return 0


@router.delete("/entrenar", response_model=int)
def remove_entrenar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    entrena = crud.entrena.get(db=db, id=id)
    if not entrena:
        raise HTTPException(status_code=404, detail="Relation not found")
    entrena = crud.entrena.remove(db=db, id=id)
    if entrena:
        return 1
    else:
        return 0


@router.delete("/entrenar_user", response_model=int)
def remove_entrenar_user(
        *,
        db: Session = Depends(deps.get_db),
        profesional: int,
        usuario: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    sql_text = text("""
        delete from tbl_entrena where fkProfesional = """ + str(profesional) + """ and fkUsuario = """ + str(usuario))
    db.execute(sql_text)
    if db.commit():
        return 1
    else:
        return 0


@router.put("/plan", response_model=schemas.Asignado)
def create_asignar(
        *,
        db: Session = Depends(deps.get_db),
        entrena_in: schemas.AsignadoCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.fkRol >= 1:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    plan = read_plan(db=db, id=entrena_in.fkSesion, current_user=current_user)  # Check model exists
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.fkCreador != current_user.id:
        raise HTTPException(status_code=400, detail="Not involved")
    return crud.asignado.create_with_validation(db=db, obj_in=entrena_in, user=current_user)


@router.delete("/plan", response_model=schemas.Asignado)
def asignar(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    asignacion = crud.asignado.get(db=db, id=id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Relation not found")
    if current_user.fkRol < 1:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    if not (asignacion.fkUsuario == current_user.id or asignacion.fkAsignador == current_user.id):
        raise HTTPException(status_code=400, detail="Not involved")
    asignacion = crud.asignado.remove(db=db, id=id)
    return asignacion


@router.post("/plan_users", response_model=schemas.Sesion)
def asignar_users(
        *,
        db: Session = Depends(deps.get_db),
        ids: List[int],
        sesionId: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    sesion = read_plan(db=db, id=sesionId, current_user=current_user)  # Check model exists
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesion not found")
    for id in ids:
        asignado = AsignadoCreate(fkUsuario=id, fkSesion=sesionId)
        crud.asignado.create(db=db, obj_in=asignado)
    sesion = read_plan(db=db, id=sesionId, current_user=current_user)  # Check model exists
    return sesion
