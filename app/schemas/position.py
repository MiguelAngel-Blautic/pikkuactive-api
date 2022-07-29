from typing import Optional

from pydantic import BaseModel


# Shared properties
class PositionBase(BaseModel):
    fldSName: Optional[str] = None
    fldSDescription: Optional[str] = None


# Properties to receive on position creation
class PositionCreate(PositionBase):
    fldSName: str


# Properties to receive on position update
class PositionUpdate(PositionBase):
    pass


# Properties shared by position stored in DB
class PositionInDBBase(PositionBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Position(PositionInDBBase):
    pass


# Properties properties stored in DB
class PositionInDB(PositionInDBBase):
    pass
