from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.schemas.cam import CamCreate, Cam
from app.schemas.data import Data, DataCreate
from app.schemas.mpu import MpuCreate, Mpu
from app.schemas.ecg import EcgCreate, Ecg


class CaptureBase(BaseModel):
    pass


class CaptureEntrada(BaseModel):
    sensor: int
    data: List[DataCreate]


# Properties to receive on movement creation
class CaptureCreate(CaptureBase):
    datos: List[CaptureEntrada]
    start: Optional[float] = 0.0
    mid: Optional[float] = 0.5
    end: Optional[float] = 1.0
    valor: Optional[float] = 1.0


# Properties to receive on movement update
class CaptureUpdate(CaptureBase):
    pass


# Properties shared by movement stored in DB
class CaptureInDBBase(CaptureBase):
    id: int
    fkOwner: int
    fldDTimeCreateTime: datetime
    datos: List[Data]
    max_value: Optional[int]
    class Config:
        orm_mode = True


# Properties to return to client
class Capture(CaptureInDBBase):
    pass


class CaptureResumen(BaseModel):
    nombre: str
    correcto: int
    fecha: datetime
    id: int

# Properties stored in DB
class CaptureInDB(CaptureInDBBase):
    pass
