from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.models.tbl_model import TrainingStatus
from app.schemas.device import DeviceCreate, Device
from app.schemas.movement import Movement, MovementCreate
from app.schemas.version import Version


class ModelBase(BaseModel):
    fldSName: Optional[str] = None
    fldSDescription: Optional[str] = None
    fldNDuration: Optional[int] = None
    fldBAutoTraining: bool = False
    fldSImage: Optional[str] = None
    fldSVideo: Optional[str] = None
    fkTipo: Optional[int] = 1


# Properties to receive on item creation
class ModelCreate(ModelBase):
    fldSName: str
    fldNDuration: int
    devices: List[DeviceCreate]
    movements: Optional[List[MovementCreate]]


# Properties to receive on item update
class ModelUpdate(ModelBase):
    pass


# Properties shared by models stored in DB
class ModelInDBBase(ModelBase):
    id: int
    fldSName: str
    fldNDuration: int
    fkOwner: int
    fkTipo: int
    fldSUrl: Optional[str] = None
    fldDTimeCreateTime: datetime
    fldSStatus: Optional[TrainingStatus] = None
    fldNProgress: Optional[int] = None
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
