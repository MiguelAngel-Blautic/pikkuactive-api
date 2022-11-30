from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# Shared properties
from app.schemas.ejercicio import Ejercicio


class AsignadoBase(BaseModel):
    fkUsuario: Optional[int] = None
    fkSesion: Optional[int] = None

# Properties to receive via API on creation
class AsignadoCreate(AsignadoBase):
    fkUsuario: int
    fkSesion: int


# Properties to receive via API on update
class AsignadoUpdate(AsignadoBase):
    fldDTimeAsignacion: Optional[datetime] = None
    fkAsignador: Optional[int] = None
    pass


class AsignadoInDBBase(AsignadoBase):
    fldDTimeAsignacion: Optional[datetime] = None
    fkAsignador: Optional[int] = None
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Asignado(AsignadoInDBBase):
    pass
