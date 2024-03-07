from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models import tbl_user
from app.schemas import UserGenerales

router = APIRouter()

@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/general", response_model=List[schemas.UserGenerales])
def get_users_generla(
        inicio: datetime,
        fin: datetime,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_superuser),
) -> Any:
    res = []
    users = db.query(tbl_user).all()
    for user in users:
        capturas = db.execute("""select count(*), max(tc.fldDTimeCreateTime) from tbl_capture tc join tbl_movement tm on (tc.fkOwner = tm.id) join tbl_model tm2 on (tm.fkOwner = tm2.id) where tm2.fkOwner = """+str(user.id)+""" and tc.fldDTimeCreateTime between '"""+str(inicio)+"""' and '"""+str(fin)+"""'""")
        entrenamientos = db.execute("""select count(*), max(tv.fldDTimeCreateTime) from tbl_version tv join tbl_model tm on (tv.fkOwner = tm.id) where tm.fkOwner = """+str(user.id)+""" and tv.fldDTimeCreateTime between '"""+str(inicio)+"""' and '"""+str(fin)+"""'""")
        consultas = db.execute("""select count(*), max(tc.fldDFecha) from tbl_consultas tc where tc.fkUser = """+str(user.id)+""" and tc.fldDFecha between '"""+str(inicio)+"""' and '"""+str(fin)+"""'""")
        capTotal = 0
        entTotal = 0
        conTotal = 0
        capUltimo = 0
        entUltimo = 0
        conUltimo = 0
        for cap in capturas:
            capTotal = cap[0]
            capUltimo = cap[1]
        for ent in entrenamientos:
            entTotal = ent[0]
            entUltimo = ent[1]
        for con in consultas:
            conTotal = con[0]
            conUltimo = con[1]
        res.append(UserGenerales(id=user.id,
                                nombre=user.fldSFullName,
                                correo=user.fldSEmail,
                                consultas=conTotal,
                                capturas=capTotal,
                                entrenamientos=entTotal,
                                ultimaConsulta=conUltimo,
                                ultimaCaptura=capUltimo,
                                ultimoEntrenamiento=entUltimo))
    return res

@router.post("/open", response_model=schemas.User)
def create_user_open(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.fldSEmail)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.post("/complete/", response_model=schemas.User)
def complete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserComplete,
) -> Any:
    """
    Complete new user.
    """
    user = crud.user.get_remote(db, id=user_in.idPlataforma)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.complete(db, obj_in=user_in)
    return user