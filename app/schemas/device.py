from typing import Optional

from pydantic import BaseModel
from app.schemas.position import Position


# Shared properties
class DeviceBase(BaseModel):
    number_device: Optional[int] = None


# Properties to receive on item creation
class DeviceCreate(DeviceBase):
    number_device: int
    position_id: int


# Properties to receive on item update
class DeviceUpdate(DeviceCreate):
    pass


# Properties shared by models stored in DB
class DeviceInDBBase(DeviceBase):
    id: int
    number_device: int
    position_id: int
    owner_id: int
    position: Optional[Position]

    class Config:
        orm_mode = True


# Properties to return to client
class Device(DeviceInDBBase):
    pass


# Properties properties stored in DB
class DeviceInDB(DeviceInDBBase):
    pass
