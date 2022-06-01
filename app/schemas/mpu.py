from typing import Optional

from pydantic import BaseModel
from datetime import datetime

# Shared properties


class MpuBase(BaseModel):
    sample: Optional[int] = None
    acc_x: Optional[float] = None
    acc_y: Optional[float] = None
    acc_z: Optional[float] = None
    gyr_x: Optional[float] = None
    gyr_y: Optional[float] = None
    gyr_z: Optional[float] = None


# Properties to receive on movement creation
class MpuCreate(MpuBase):
    n_device: int
    sample: int
    acc_x: float
    acc_y: float
    acc_z: float
    gyr_x: float
    gyr_y: float
    gyr_z: float


# Properties to receive on movement update
class MpuUpdate(MpuBase):
    pass


# Properties shared by movement stored in DB
class MpuInDBBase(MpuBase):
    owner_id: int
    device_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Mpu(MpuInDBBase):
    pass


# Properties properties stored in DB
class MpuInDB(MpuInDBBase):
    pass
