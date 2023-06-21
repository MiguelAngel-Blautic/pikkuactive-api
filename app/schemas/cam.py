from typing import Optional

from pydantic import BaseModel
from datetime import datetime

# Shared properties


class CamBase(BaseModel):
    fldNSample: Optional[int] = None
    fldFX: Optional[float] = None
    fldFY: Optional[float] = None
    fkPosicion: Optional[int] = None
    fkDevice: Optional[int] = None


# Properties to receive on movement creation
class CamCreate(CamBase):
    fldNSample: int
    fldFX: float
    fldFY: float
    fkPosicion: int
    fkDevice: int


# Properties to receive on movement update
class CamUpdate(CamBase):
    pass


# Properties shared by movement stored in DB
class CamInDBBase(CamBase):
    fkOwner: int

    class Config:
        orm_mode = True


# Properties to return to client
class Cam(CamInDBBase):
    pass


# Properties properties stored in DB
class CamInDB(CamInDBBase):
    pass
