from typing import Optional

from pydantic import BaseModel
from datetime import datetime


# Shared properties
class MovementBase(BaseModel):
    fldSLabel: Optional[str] = None
    fldSDescription: Optional[str] = None


# Properties to receive on movement creation
class MovementCreate(MovementBase):
    fldSLabel: str


# Properties to receive on movement update
class MovementUpdate(MovementBase):
    pass


# Properties shared by movement stored in DB
class MovementInDBBase(MovementBase):
    id: int
    fldSLabel: str
    fldSDescription: Optional[str]
    fkOwner: int
    fldDTimeCreateTime: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class Movement(MovementInDBBase):
    pass


# Properties properties stored in DB
class MovementInDB(MovementInDBBase):
    pass
