from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# Shared properties
class PlanBase(BaseModel):
    fldSNombre: str


# Properties to receive via API on creation
class PlanCreate(PlanBase):
    fkCliente: int


class PlanUpdate(PlanBase):
    pass


class Plan(PlanBase):
    fkCreador: int
    fkCliente: Optional[int] = None
    id: int
    class Config:
        orm_mode = True


class EntrenamientoDetalle(BaseModel):
    nombre: str
    id: int
    adherencia: float
    progreso: float
    fechas: List[date]


class EjercicioDetalle(BaseModel):
    nombre: str
    id: int
    adherencia: float

class PlanDetalle(BaseModel):
    nombre: str
    id: int
    inicio: Optional[date]
    fin: Optional[date]
    adherencia: float
    progreso: float
    entrenamientos: List[EntrenamientoDetalle]
    ejercicios: List[EjercicioDetalle]
