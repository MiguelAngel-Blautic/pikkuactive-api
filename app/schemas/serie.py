from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.schemas import Ejercicio


# Shared properties
class SerieBase(BaseModel):
    fldSDescripcion: str
    fldNDescanso: int
    fldNRepeticiones: int
    fldBSimultanea: int


# Properties to receive via API on creation
class SerieCreate(SerieBase):
    fkBloque: int
    pass


class SerieUpdate(SerieBase):
    pass


class Serie(SerieBase):
    fkBloque: int
    fldNOrden: int
    id: int
    class Config:
        orm_mode = True


class Seriecompleta(Serie):
    ejercicios: List[Ejercicio]