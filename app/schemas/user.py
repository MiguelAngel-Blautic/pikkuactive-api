from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    fldSEmail: Optional[EmailStr] = None
    fldBActive: Optional[bool] = True
    fldNSexo: Optional[int] = None
    fldTNacimiento: Optional[datetime] = None
    fldSTelefono: Optional[str] = None
    fldSImagen: Optional[str] = None
    fkRol: Optional[int] = 1
    fldSFullName: Optional[str] = None


class UserComplete(BaseModel):
    fldBActive: Optional[bool] = True
    fldNSexo: Optional[int] = None
    fldTNacimiento: Optional[datetime] = None
    fldSTelefono: Optional[str] = None
    fldSImagen: Optional[str] = None
    fkRol: Optional[int] = 1
    fldSFullName: Optional[str] = None
    idPlataforma: Optional[int] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    fldSEmail: EmailStr
    fldSHashedPassword: str
    fkRol: int


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    fldSFcmToken: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    estado: int = 0
    idRelacion: Optional[int] = 0


class UserGenerales(BaseModel):
    id: int
    nombre: str
    consultas: int
    capturas: int
    entrenamientos: int
    ultimaConsulta: Optional[datetime]
    ultimaCaptura: Optional[datetime]
    ultimoEntrenamiento: Optional[datetime]


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    fldSHashedPassword: str
