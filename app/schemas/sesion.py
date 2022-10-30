from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

# Shared properties
from app.schemas.ejercicio import Ejercicio, EjercicioResumen


class SesionBase(BaseModel):
    fldSNombre: Optional[str] = None
    fkCreador: Optional[int] = None
    fldBGenerico: Optional[int] = None


# Properties to receive via API on creation
class SesionCreate(SesionBase):
    fldSNombre: str
    fkCreador: Optional[int]
    fldBGenerico: Optional[int] = None


# Properties to receive via API on update
class SesionUpdate(SesionBase):
    pass


class SesionInDBBase(SesionBase):
    id: Optional[int] = None
    ejercicios: Optional[List[Ejercicio]] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Sesion(SesionInDBBase):
    pass
