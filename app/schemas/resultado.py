from datetime import datetime
from typing import Optional

from pydantic import BaseModel



class ResultadoBase(BaseModel):
    fldFValor: Optional[float] = None
    fldDTimeFecha: Optional[datetime] = None
    fldNIntento: Optional[int] = None

# Properties to receive via API on creation
class ResultadoCreate(ResultadoBase):
    fldFValor: float
    fldDTimeFecha: Optional[datetime] = None
    fldNIntento: int

# Properties to receive via API on update
class ResultadoUpdate(ResultadoBase):
    pass


class ResultadoInDBBase(ResultadoBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Resultado(ResultadoInDBBase):
    pass