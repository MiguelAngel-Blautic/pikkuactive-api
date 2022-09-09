from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    if current_user.fkRol == 1:
        users = crud.user.get_centros(db, user=current_user.id, skip=skip, limit=limit)
    if current_user.fkRol == 2:
        users = crud.user.get_clientes(db, user=current_user.id, rol=current_user.fkRol)
    if current_user.fkRol == 3:
        users = crud.user.get_clientes(db, user=current_user.id, rol=current_user.fkRol)
    if current_user.fkRol == 4:
        print("Dentro")
        users = crud.user.get_multi(db, skip=skip, limit=limit)

    return users


@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.tbl_user = Depends(deps.get_current_active_superuser),
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
    if settings.EMAILS_ENABLED and user_in.fldSEmail:
        send_new_account_email(
            email_to=user_in.fldSEmail, username=user_in.fldSEmail, password=user_in.fldSHashedPassword
        )
    return user


@router.put("/token", response_model=schemas.User)
def send_fcm_token(
    *,
    fcm_token: str,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send fcm token own user.
    """

    if fcm_token is not None:
        current_user.fldSFcmToken = fcm_token
    db.commit()
    return current_user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: str = Body(None),
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.fldSFullName = full_name
    if email is not None:
        user_in.fldSEmail = email
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
    user_in.fkRol = 1
    user = crud.user.create(db, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.fldSEmail:
        send_new_account_email(
            email_to=user_in.fldSEmail, username=user_in.fldSEmail, password=user_in.fldSHashedPassword
        )
    return user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a user.
    """
    if (user_id != current_user.id) and (current_user.fkRol < 3):
        raise HTTPException(
            status_code=400,
            detail="Only can update your user",
        )
    user = crud.user.get(db, id=user_id)
    if not user_in.password:
        user_in.password = ""
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user_in.fldSFcmToken = user.fldSFcmToken
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user
