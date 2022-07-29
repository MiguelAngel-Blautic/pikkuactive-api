from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

# Shared properties
from app.schemas.history import History


class VersionBase(BaseModel):
    fldFAccuracy: Optional[float] = None
    fldNEpoch: Optional[int] = None
    fldFLoss: Optional[float] = None
    fldSOptimizer: Optional[str] = None
    fldFLearningRate: Optional[float] = None


# Properties to receive on movement creation
class VersionCreate(VersionBase):
    fldFAccuracy: float
    fldNEpoch: int
    fldFLoss: float
    fldSOptimizer: str
    fldFLearningRate: float


# Properties to receive on movement update
class VersionUpdate(VersionBase):
    pass


# Properties shared by movement stored in DB
class VersionInDBBase(VersionBase):
    id: int
    fkOwner: int
    fldDTimeCreateTime: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class Version(VersionInDBBase):
    pass


# Properties properties stored in DB
class VersionInDB(VersionInDBBase):
    pass
