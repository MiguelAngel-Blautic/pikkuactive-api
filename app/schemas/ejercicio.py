from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.schemas import RegistroEjercicio, RegistroEjercicioDB


# Shared properties
class EjercicioBase(BaseModel):
    fldNDescanso: int
    fldNRepeticiones: Optional[int]
    fldNDistancia: Optional[int]
    fldNDuracion: Optional[int]
    fldNDuracionEfectiva: Optional[int]
    fldFVelocidad: Optional[float]
    fldFUmbral: Optional[float]
    fkModelo: Optional[int]
    fldSToken: Optional[str]


# Properties to receive via API on creation
class EjercicioCreate(EjercicioBase):
    fkSerie: int
    registros: List[int]
    pass


class EjercicioUpdate(EjercicioBase):
    pass


class Ejercicio(EjercicioBase):
    fkSerie: int
    fldNOrden: int
    id: int

    class Config:
        orm_mode = True


class EjercicioTipos(Ejercicio):
    tipodatos: List[RegistroEjercicioDB]


class EjercicioDetalles(BaseModel):
    tipo: int
    adherencia: float
    fldNOrden: int
    id: int
    fldNDescanso: int
    fldNRepeticiones: Optional[int]
    fldNDuracion: Optional[int]
    fldNDistancia: Optional[int]
    fldFVelocidad: Optional[float]
    fkModelo: Optional[int]
    fldSToken: Optional[str]
    items: List['EjercicioDetalles']
    completo: float
    nombre: str


EjercicioDetalles.update_forward_refs()


class Resultado(BaseModel):
    nombre: str
    adherencia: int
    completo: float
    id: int
