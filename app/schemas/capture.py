from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.schemas.mpu import MpuCreate, Mpu
from app.schemas.ecg import EcgCreate, Ecg


class CaptureBase(BaseModel):
    pass


# Properties to receive on movement creation
class CaptureCreate(CaptureBase):
    mpu: List[MpuCreate]
    ecg: List[EcgCreate]


# Properties to receive on movement update
class CaptureUpdate(CaptureBase):
    pass


# Properties shared by movement stored in DB
class CaptureInDBBase(CaptureBase):
    id: int
    owner_id: int
    create_time: datetime
    mpu: List[Mpu]
    ecg: List[Ecg]
    max_value: Optional[int]
    class Config:
        orm_mode = True


# Properties to return to client
class Capture(CaptureInDBBase):
    pass


# Properties properties stored in DB
class CaptureInDB(CaptureInDBBase):
    pass
