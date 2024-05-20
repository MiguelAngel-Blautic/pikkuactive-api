from datetime import date
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.schemas import Bloquecompleto


# Shared properties
class EntrenamientoBase(BaseModel):
    fldSNombre: str


# Properties to receive via API on creation
class EntrenamientoCreate(EntrenamientoBase):
    pass


class EntrenamientoUpdate(EntrenamientoBase):
    fldDDia: Optional[date] = None


class Entrenamiento(EntrenamientoBase):
    fkPlan: Optional[int] = None
    fkPadre: Optional[int] = None
    fkCreador: int
    fldDDia: Optional[date] = None
    id: int
    class Config:
        orm_mode = True


class EntrenamientoCompleto(Entrenamiento):
    bloques: List[Bloquecompleto]
