from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import tbl_user

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(tbl_user).filter(tbl_user.fldSEmail == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.fldSHashedPassword):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires, it_expire=False
        ),
        "token_type": "bearer",
        "rol": user.fkRol,
        "id": user.id,
        "fullName": user.fldSFullName
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.tbl_user = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user
