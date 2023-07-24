from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties


class MpuBase(BaseModel):
    fldNSample: Optional[int] = None
    fldFAccX: Optional[float] = None
    fldFAccY: Optional[float] = None
    fldFAccZ: Optional[float] = None
    fldFGyrX: Optional[float] = None
    fldFGyrY: Optional[float] = None
    fldFGyrZ: Optional[float] = None


# Properties to receive on movement creation
class MpuCreate(MpuBase):
    fkDevice: int
    fldNSample: int
    fldFAccX: float
    fldFAccY: float
    fldFAccZ: float
    fldFGyrX: float
    fldFGyrY: float
    fldFGyrZ: float


class MpuListItem(BaseModel):
    fldFAccX: float
    fldFAccY: float
    fldFAccZ: float
    fldFGyrX: float
    fldFGyrY: float
    fldFGyrZ: float


class MpuEstadisticas(BaseModel):
    media: float
    std: float
    min: float
    max: float


class MpuList(BaseModel):
    mpu: List[MpuListItem] = []


# Properties to receive on movement update
class MpuUpdate(MpuBase):
    pass


# Properties shared by movement stored in DB
class MpuInDBBase(MpuBase):
    fkOwner: int
    fkDevice: int

    class Config:
        orm_mode = True


# Properties to return to client
class Mpu(MpuInDBBase):
    pass


# Properties properties stored in DB
class MpuInDB(MpuInDBBase):
    pass
