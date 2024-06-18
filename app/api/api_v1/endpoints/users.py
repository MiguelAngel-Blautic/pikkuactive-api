from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models import tbl_user, tbl_entrena
from app.schemas.user import UserDetails

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve users.
    """
    users = []
    if current_user.fkRol == 1:
        idUsers = db.query(tbl_entrena).filter(tbl_entrena.fkProfesional == current_user.id).all()
        users = db.query(tbl_user).filter(tbl_user.id.in_([user.id for user in idUsers])).all()
    return users


@router.get("/comprobar")
def check_user(
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve users.
    """
    if current_user.idPlataforma == None:
        return 0
    else:
        return current_user.idPlataforma


@router.post("/", response_model=schemas.User)
def create_user(
        *,
        db: Session = Depends(deps.get_db),
        user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = db.query(tbl_user).filter(tbl_user.fldSEmail == user_in.fldSEmail).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = db.query(tbl_user).filter(tbl_user.idPlataforma == user_in.idPlataforma).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this user already exists in the system.",
        )
    newUser = tbl_user(fldSFullName=user_in.fldSFullName,
                       fldSEmail=user_in.fldSEmail,
                       fldSDireccion=user_in.fldSDireccion,
                       fldSTelefono=user_in.fldSTelefono,
                       fldSImagen=user_in.fldSImagen,
                       idPlataforma=user_in.idPlataforma,
                       fkRol=user_in.fkRol)
    db.add(newUser)
    db.commit()
    db.refresh(newUser)
    return newUser


@router.put("/", response_model=schemas.User)
def update_user(
        *,
        db: Session = Depends(deps.get_db),
        user_in: schemas.UserUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update own user.
    """
    current_user.fldSDireccion = user_in.fldSDireccion
    current_user.fldSTelefono = user_in.fldSTelefono
    current_user.fldSImagen = user_in.fldSImagen
    current_user.fldSFullName = user_in.fldSFullName
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me", response_model=schemas.User)
def read_user_me(
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/platform/{user_id}", response_model=schemas.UserDetails)
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
    adherencia = 0
    completado = 0
    actual = datetime.now()
    for row in res:
        if row[2] <= actual.date() <= row[3]:
            diaAct = actual.date() - row[2]
            dias = row[3] - row[2]
            completado = (100 * diaAct.days) / dias.days
            sql = text("""
            SELECT count(*)
                from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
                join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                join tbl_planes tp on (tp.id = ten.fkPlan) where tp.id=""" + str(
                row[0]) + """ and tre.fkTipoDato = 2; """)
            total = db.execute(sql)
            for t in total:
                adherencia = (t[0] * 100) / row[1]
    return UserDetails(fldSEmail=user.fldSEmail,
                       id=user.id,
                       fkRol=user.fkRol,
                       idPlataforma=user.idPlataforma,
                       fldSDireccion=user.fldSDireccion,
                       fldSTelefono=user.fldSTelefono,
                       fldSImagen=user.fldSImagen,
                       fldSFullName=user.fldSFullName,
                       adherencia=adherencia,
                       completado=completado)


@router.get("/{user_id}", response_model=schemas.UserDetails)
def read_user_by_id(
        user_id: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(tbl_user).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="The user doesn't exist")
    sql = text("""
        SELECT tp.id, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia)
    from tbl_ejercicios te
    join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
    join tbl_planes tp on (tp.id = ten.fkPlan) where ten.fldDDia is not null and tp.fkCliente = """ + str(
        user.id) + """ group by tp.id; """)
    res = db.execute(sql)
    adherencia = 0
    completado = 0
    actual = datetime.now()
    for row in res:
        if row[2] <= actual.date() <= row[3]:
            diaAct = actual.date() - row[2]
            dias = row[3] - row[2]
            completado = (100 * diaAct.days) / dias.days
            sql = text("""
            SELECT count(*)
                from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
                join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                join tbl_planes tp on (tp.id = ten.fkPlan) where tp.id=""" + str(
                row[0]) + """ and tre.fkTipoDato = 2; """)
            total = db.execute(sql)
            for t in total:
                adherencia = (t[0] * 100) / row[1]
    return UserDetails(fldSEmail=user.fldSEmail,
                       id=user.id,
                       fkRol=user.fkRol,
                       idPlataforma=user.idPlataforma,
                       fldSDireccion=user.fldSDireccion,
                       fldSTelefono=user.fldSTelefono,
                       fldSImagen=user.fldSImagen,
                       fldSFullName=user.fldSFullName,
                       adherencia=adherencia,
                       completado=completado)


@router.get("/list/", response_model=List[schemas.UserDetails])
def read_user_by_id_list(
        users: List[int],
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    for user_id in users:
        user = db.query(tbl_user).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="The user doesn't exist")
        sql = text("""
            SELECT tp.id, sum(te.fldNRepeticioneS * ts.fldNRepeticiones), min(ten.fldDDia), max(ten.fldDDia)
        from tbl_ejercicios te
        join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
        join tbl_planes tp on (tp.id = ten.fkPlan) where ten.fldDDia is not null and tp.fkCliente = """ + str(
            user.id) + """ group by tp.id; """)
        res = db.execute(sql)
        adherencia = 0
        completado = 0
        actual = datetime.now()
        for row in res:
            if row[2] <= actual.date() <= row[3]:
                diaAct = actual.date() - row[2]
                dias = row[3] - row[2]
                completado = (100 * diaAct.days) / dias.days
                sql = text("""
                SELECT count(*)
                    from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
                    join tbl_series ts on (ts.id = te.fkSerie) join tbl_bloques tb on (tb.id = ts.fkBloque) join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
                    join tbl_planes tp on (tp.id = ten.fkPlan) where tp.id=""" + str(
                    row[0]) + """ and tre.fkTipoDato = 2; """)
                total = db.execute(sql)
                for t in total:
                    adherencia = (t[0] * 100) / row[1]
        response.append(UserDetails(fldSEmail=user.fldSEmail,
                           id=user.id,
                           fkRol=user.fkRol,
                           idPlataforma=user.idPlataforma,
                           fldSDireccion=user.fldSDireccion,
                           fldSTelefono=user.fldSTelefono,
                           fldSImagen=user.fldSImagen,
                           fldSFullName=user.fldSFullName,
                           adherencia=adherencia,
                           completado=completado))
    return response