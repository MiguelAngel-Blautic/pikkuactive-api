from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ResultadoBase(BaseModel):
    fldFValor: Optional[float] = None
    fldDTimeFecha: Optional[datetime] = None
    fldNIntento: Optional[int] = None
    fldFUmbral: Optional[float] = None
    fkUser: Optional[int] = None


# Properties to receive via API on creation
class ResultadoCreate(ResultadoBase):
    fldFValor: float
    fldDTimeFecha: Optional[datetime] = None
    fldNIntento: int
    fldFUmbral: float


# Properties to receive via API on update
class ResultadoUpdate(ResultadoBase):
    pass


class ResultadoInDBBase(ResultadoBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Resultado(ResultadoInDBBase):
    pass


class ResultadoEjercicio(BaseModel):
    id: int
    nombre: str
    resultados: List[Resultado]


class ResultadoTUmbral(BaseModel):
    id: int
    ejercicios: List[ResultadoEjercicio]


class ResultadoUsuario(BaseModel):
    id: int
    nombre: str
    tumbrales: List[ResultadoTUmbral]


class ResultadosSesion(BaseModel):
    id: int
    usuarios: List[ResultadoUsuario]
