from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime


# Shared properties


class DataCreate(BaseModel):
    fldNSample: int
    fldFValor: float


class DataDb(DataCreate):
    fkCaptura: int
    fkDispositivoSensor: int

    class Config:
        orm_mode = True


class Data(DataDb):
    pass
