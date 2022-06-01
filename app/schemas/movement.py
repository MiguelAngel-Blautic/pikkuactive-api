from typing import Optional

from pydantic import BaseModel
from datetime import datetime


# Shared properties
class MovementBase(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on movement creation
class MovementCreate(MovementBase):
    label: str


# Properties to receive on movement update
class MovementUpdate(MovementBase):
    pass


# Properties shared by movement stored in DB
class MovementInDBBase(MovementBase):
    id: int
    label: str
    description: Optional[str]
    owner_id: int
    create_time: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class Movement(MovementInDBBase):
    pass


# Properties properties stored in DB
class MovementInDB(MovementInDBBase):
    pass
