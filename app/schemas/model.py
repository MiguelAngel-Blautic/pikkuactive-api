from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.models.model import TrainingStatus
from app.schemas.device import DeviceCreate, Device
from app.schemas.movement import Movement, MovementCreate
from app.schemas.version import Version


class ModelBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    auto_training: bool = False
    image: Optional[str] = None
    video: Optional[str] = None


# Properties to receive on item creation
class ModelCreate(ModelBase):
    name: str
    duration: int
    devices: List[DeviceCreate]
    movements: Optional[List[MovementCreate]]


# Properties to receive on item update
class ModelUpdate(ModelBase):
    pass


# Properties shared by models stored in DB
class ModelInDBBase(ModelBase):
    id: int
    name: str
    duration: int
    owner_id: int
    url: Optional[str] = None
    create_time: datetime
    status: Optional[TrainingStatus] = None
    progress: Optional[int] = None
    movements: List[Movement] = []
    devices: List[Device] = []
    versions: List[Version] = []

    class Config:
        orm_mode = True


# Properties to return to client
class Model(ModelInDBBase):
    pass


# Properties properties stored in DB
class ModelInDB(ModelInDBBase):
    pass
