from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.models.tbl_model import TrainingStatus
from app.schemas.device import DeviceCreate, Device, DeviceSensor, DeviceSensorCreate
from app.schemas.movement import Movement, MovementCreate
from app.schemas.version import Version


class ModelStadistics(BaseModel):
    sample: int
    media: float
    std: float


class ModelStadisticsSensor(BaseModel):
    id: int
    nombre: str
    datos: List[ModelStadistics]


class ModelBase(BaseModel):
    fldSName: Optional[str] = None
    fldSDescription: Optional[str] = None
    fldNDuration: Optional[int] = None
    fldBPublico: Optional[int] = 0
    fkCategoria: Optional[int] = None
    fldFPrecio: Optional[float] = 0
    fldSImage: Optional[str] = None
    fldSVideo: Optional[str] = None
    fkTipo: Optional[int] = 1


# Properties to receive on item creation
class ModelCreate(ModelBase):
    fldSName: str
    fldNDuration: int
    devices: List[DeviceCreate]
    dispositivos: List[DeviceSensorCreate] = []


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
    dispositivos: List[DeviceSensor] = []

    class Config:
        orm_mode = True


# Properties to return to client
class Model(ModelInDBBase):
    pass


# Properties properties stored in DB
class ModelInDB(ModelInDBBase):
    pass
