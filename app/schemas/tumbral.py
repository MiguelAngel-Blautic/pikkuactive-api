from typing import Optional, List

from pydantic import BaseModel

from app.schemas.resultado import Resultado


class TumbralBase(BaseModel):
    fldSNombre: Optional[str] = None

# Properties to receive via API on creation
class TumbralCreate(TumbralBase):
    fldSNombre: str


# Properties to receive via API on update
class TumbralUpdate(TumbralBase):
    pass


class TumbralInDBBase(TumbralBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Tumbral(TumbralInDBBase):
    pass
