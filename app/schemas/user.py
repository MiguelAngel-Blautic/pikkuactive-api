from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    fldSDireccion: Optional[str] = None
    fldSTelefono: Optional[str] = None
    fldSImagen: Optional[str] = None
    fldSFullName: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    fldSEmail: EmailStr
    idPlataforma: int
    fkRol: int
    idPlataforma: int


class UserUpdate(UserBase):
    pass


class User(UserBase):
    fldSEmail: EmailStr
    id: int
    fkRol: int
    idPlataforma: int
    class Config:
        orm_mode = True
