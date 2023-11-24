from typing import Optional

from pydantic import BaseModel
from app.schemas.position import Position


# Shared properties
class DeviceBase(BaseModel):
    fldNNumberDevice: Optional[int] = None



class DeviceSensorCreate(BaseModel):
    fkPosicion: int
    fkSensor: int


class DeviceSensor(BaseModel):
    id: int
    fkPosicion: int
    fkSensor: int
    fkOwner: int
    class Config:
        orm_mode = True


# Properties to receive on item creation
class DeviceCreate(DeviceBase):
    fldNNumberDevice: int
    fldNSensores: Optional[int] = 1
    fkPosition: int


# Properties to receive on item update
class DeviceUpdate(DeviceCreate):
    pass


# Properties shared by models stored in DB
class DeviceInDBBase(DeviceBase):
    id: int
    fldNNumberDevice: int
    fkPosition: int
    fkOwner: int
    position: Optional[Position]

    class Config:
        orm_mode = True


# Properties to return to client
class Device(DeviceInDBBase):
    pass


# Properties properties stored in DB
class DeviceInDB(DeviceInDBBase):
    class Config:
        orm_mode = True
