from typing import Optional, List, Any

from pydantic import BaseModel
from datetime import datetime

from scipy.constants import blob
from sqlalchemy import LargeBinary

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
    idPosicion: Optional[int] = None


class ModelBase(BaseModel):
    fldSName: Optional[str] = None
    fldSDescription: Optional[str] = None
    fldNDuration: Optional[int] = None
    fldBPublico: Optional[int] = 0
    fkCategoria: Optional[int] = None
    fldFPrecio: Optional[float] = 0
    fkImagen: Optional[int] = None
    fkVideo: Optional[int] = None
    fkTipo: Optional[int] = 1


# Properties to receive on item creation
class ModelCreate(ModelBase):
    fldSName: str
    fldNDuration: int
    devices: List[DeviceCreate]
    dispositivos: List[DeviceSensorCreate] = []
    imagen: Optional[bytes] = None


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
    imagen: Optional[bytes] = None
    video: Optional[bytes] = None
    tuyo: Optional[int] = 0

    class Config:
        orm_mode = True


# Properties to return to client
class Model(ModelInDBBase):
    pass


# Properties properties stored in DB
class ModelInDB(ModelInDBBase):
    pass
