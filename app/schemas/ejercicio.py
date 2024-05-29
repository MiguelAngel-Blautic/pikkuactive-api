from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Dato(BaseModel):
    sensor: int
    valor: float
    hora: datetime


class Marca(BaseModel):
    valor: int
    hora: datetime


# Shared properties
class Sesion(BaseModel):
    edad: Optional[int] = None
    altura: Optional[int] = None
    peso: Optional[float] = None
    sexo: Optional[int] = None
    datos: List[Dato]
    etiquetas: List[Marca]
    fases: List[Marca]
    inicio: datetime
