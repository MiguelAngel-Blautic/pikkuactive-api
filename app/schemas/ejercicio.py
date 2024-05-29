from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class EjercicioBase(BaseModel):
    fldNDescanso: int
    fldNRepeticiones: Optional[int]
    fldNDuracion: Optional[int]
    fldFVelocidad: Optional[float]
    fldFUmbral: Optional[float]
    fkModelo: Optional[int]
    fldSToken: Optional[str]


# Properties to receive via API on creation
class EjercicioCreate(EjercicioBase):
    fkSerie: int
    pass


class EjercicioUpdate(EjercicioBase):
    pass


class Ejercicio(EjercicioBase):
    fkSerie: int
    fldNOrden: int
    id: int
    class Config:
        orm_mode = True
