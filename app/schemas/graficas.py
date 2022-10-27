from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

# Shared properties
from app.schemas import Plan, User
from app.schemas.ejercicio import Ejercicio

from app.db.base_class import Base

class grafico1(BaseModel):
    ejercicio: str = ""
    id_ejercicio: int = 0
    repeticiones: int = 0


class grafico2(BaseModel):
    totales: int = 0
    correctas: int = 0


class grafico3(BaseModel):
    ejercicio: str = ""
    id_ejercicio: int = 0
    objetivo: int = 0
    progreso: int = 0
    fallidos: int = 0


class grafico4(BaseModel):
    ejercicios: str = ""
    id_ejercicio: int = 0
    repeticiones: int = 0
    dia: Optional[datetime] = None

class grafico5(BaseModel):
    plan: str = ""
    pla_id: int = 0
    objetivo: int = 0
    progreso: int = 0


class GraficasBase(BaseModel):
    grafico1: Optional[List[grafico1]] = None
    grafico2: Optional[grafico2] = None
    grafico3: Optional[List[grafico3]] = None
    grafico4: Optional[List[List[grafico4]]] = None
    grafico5: Optional[List[grafico5]] = None


# Properties to return to client
class Graficas(GraficasBase):
    pass
