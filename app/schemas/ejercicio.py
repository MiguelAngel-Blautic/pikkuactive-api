from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

# Shared properties
from app.schemas import Model
from app.schemas.umbral import Umbral, UmbralCreate


class EjercicioBase(BaseModel):
    fkEjercicio: Optional[int] = None
    ejercicio: Optional[Model] = None
    fldNRepeticiones: Optional[int] = None
    fldDDia: Optional[datetime] = None


# Properties to receive via API on creation
class EjercicioCreate(EjercicioBase):
    fkEjercicio: int
    umbrales: List[UmbralCreate]
    fldNRepeticiones: int


class EjercicioResumen(EjercicioBase):
    imagen: Optional[str] = None
    nombre: Optional[str] = None
    id: Optional[int] = None
    umbral: Optional[float] = None
    progreso: Optional[int] = None


# Properties to receive via API on update
class EjercicioUpdate(EjercicioBase):
    fkPlan: Optional[int] = None
    pass


class EjercicioInDBBase(EjercicioBase):
    id: Optional[int] = None
    umbrales: Optional[List[Umbral]] = None
    fkPlan: Optional[int] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Ejercicio(EjercicioInDBBase):
    pass
