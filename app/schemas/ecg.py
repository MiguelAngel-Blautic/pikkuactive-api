from typing import Optional, List
from pydantic import BaseModel


# Aditional Class
# Ecg
class EcgBase(BaseModel):
    sample: int
    time: int
    data: float
    type: Optional[str] = None


class EcgCreate(EcgBase):
    sample: int
    time: int
    data: float
    type: Optional[str] = None
    n_device: int


# Properties shared by movement stored in DB
class EcgInDBBase(EcgBase):
    owner_id: int
    device_id: int

    class Config:
        orm_mode = True


class Ecg(EcgInDBBase):
    class Config:
        orm_mode = True
