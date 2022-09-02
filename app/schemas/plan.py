from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

# Shared properties
from app.schemas.ejercicio import Ejercicio, EjercicioResumen


class PlanBase(BaseModel):
    fldSNombre: Optional[str] = None
    fkCreador: Optional[int] = None
    fldBGenerico: bool = True


# Properties to receive via API on creation
class PlanCreate(PlanBase):
    fldSNombre: str
    fkCreador: int
    fldBGenerico: bool


class PlanResumen(PlanBase):
    ejercicios: Optional[List[EjercicioResumen]] = None
    id: Optional[int] = None


# Properties to receive via API on update
class PlanUpdate(PlanBase):
    pass


class PlanInDBBase(PlanBase):
    id: Optional[int] = None
    ejercicios: Optional[List[Ejercicio]] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Plan(PlanInDBBase):
    pass
