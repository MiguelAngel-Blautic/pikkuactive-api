from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.schemas.history import History


class Grafica1(BaseModel):
    id_ejercicio: int
    nombre_ejercicio: str
    repeticiones: int


class Grafica2(BaseModel):
    total_correcto: int
    total: int


class Grafica3(BaseModel):
    id_ejercicio: int
    nombre_ejercicio: str
    intentos: int
    correctos: int


class Grafica4Aux(BaseModel):
    id_ejercicio: int
    nombre_ejercicio: str
    repeticiones: int


class Grafica4(BaseModel):
    fecha: datetime
    ejercicios: List[Grafica4Aux]


class Grafica5(BaseModel):
    id_plan: int
    nombre_plan: str
    objetivo: int
    repeticiones: int


class GraficaBase(BaseModel):
    grafica1: List[Grafica1]
    grafica2: Grafica2
    grafica3: List[Grafica3]
    grafica4: List[Grafica4]
    grafica5: List[Grafica5]


# Properties properties stored in DB
class Grafica(GraficaBase):
    pass
