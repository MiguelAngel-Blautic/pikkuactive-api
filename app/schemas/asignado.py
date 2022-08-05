from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# Shared properties
from app.schemas import Plan, User
from app.schemas.ejercicio import Ejercicio


class AsignadoBase(BaseModel):
    fkUsuario: Optional[int] = None
    fkPlan: Optional[int] = None
    fldDTimeAsignacion: Optional[datetime] = None

# Properties to receive via API on creation
class AsignadoCreate(AsignadoBase):
    fkUsuario: int
    fkPlan: int


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
