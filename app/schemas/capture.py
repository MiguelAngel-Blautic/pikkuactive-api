from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.schemas.cam import CamCreate, Cam
from app.schemas.mpu import MpuCreate, Mpu
from app.schemas.ecg import EcgCreate, Ecg


class CaptureBase(BaseModel):
    pass


# Properties to receive on movement creation
class CaptureCreate(CaptureBase):
    mpu: List[MpuCreate]
    ecg: List[EcgCreate]
    cam: List[CamCreate]


# Properties to receive on movement update
class CaptureUpdate(CaptureBase):
    pass


# Properties shared by movement stored in DB
class CaptureInDBBase(CaptureBase):
    id: int
    fkOwner: int
    fldDTimeCreateTime: datetime
    mpu: List[Mpu]
    ecg: List[Ecg]
    cam: List[Cam]
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

# Properties properties stored in DB
class CaptureInDB(CaptureInDBBase):
    pass
