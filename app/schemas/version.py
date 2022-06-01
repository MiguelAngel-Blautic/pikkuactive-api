from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.schemas.history import History


class VersionBase(BaseModel):
    accuracy: Optional[float] = None
    epoch: Optional[int] = None
    loss: Optional[float] = None
    optimizer: Optional[str] = None
    learning_rate: Optional[float] = None


# Properties to receive on movement creation
class VersionCreate(VersionBase):
    accuracy: float
    epoch: int
    loss: float
    optimizer: str
    learning_rate: float


# Properties to receive on movement update
class VersionUpdate(VersionBase):
    pass


# Properties shared by movement stored in DB
class VersionInDBBase(VersionBase):
    id: int
    owner_id: int
    create_time: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class Version(VersionInDBBase):
    pass


# Properties properties stored in DB
class VersionInDB(VersionInDBBase):
    pass
