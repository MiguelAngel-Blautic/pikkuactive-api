from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime


# Shared properties


class DataCreate(BaseModel):
    fldNSample: int
    fldFValor: float
    fldFValor2: Optional[float] = None
    fldFValor3: Optional[float] = None


class DataDb(DataCreate):
    fkCaptura: int
    fkDispositivoSensor: int
    idPosicion: Optional[int] = None

    class Config:
        orm_mode = True


class Data(DataDb):
    pass
