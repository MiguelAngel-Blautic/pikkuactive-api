from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models import tbl_user, tbl_entrena

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
        users = db.query(tbl_user).filter(tbl_user .id.in_([user.id for user in idUsers])).all()
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
    newUser = tbl_user( fldSFullName = user_in.fldSFullName,
                        fldSEmail = user_in.fldSEmail,
                        fldSDireccion = user_in.fldSDireccion,
                        fldSTelefono = user_in.fldSTelefono,
                        fldSImagen = user_in.fldSImagen,
                        idPlataforma = user_in.idPlataforma,
                        fkRol = user_in.fkRol)
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


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    relacion = db.query(tbl_entrena).filter(tbl_entrena.fkProfesional == current_user.id).filter(tbl_entrena.fkUsuario == user_id).first()
    if not relacion:
        raise HTTPException(status_code=404, detail="The user doesn't have enough privileges")
    user = db.query(tbl_user).get(user_id)
    return user