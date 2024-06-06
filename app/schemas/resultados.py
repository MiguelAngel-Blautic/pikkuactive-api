from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class TipoDato(BaseModel):
    fldFNombre: int
    id: int


# Properties to receive via API on creation
class RegistroEjercicio(BaseModel):
    fkEjercicio: int
    fkTipoDato: int


class RegistroEjercicioDB(RegistroEjercicio):
    id: int


class Resultado(BaseModel):
    fkRegistro: int
    fldFValor: float
    fldDTime: datetime


class ResultadoBD(Resultado):
    id: int
