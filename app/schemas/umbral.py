from typing import Optional, List

from pydantic import BaseModel

from app.schemas.resultado import Resultado
from app.schemas.tumbral import Tumbral


class UmbralBase(BaseModel):
    fldFValor: Optional[float] = None
    fkTipo: Optional[int] = None

# Properties to receive via API on creation
class UmbralCreate(UmbralBase):
    fkTipo: int
    fldFValor: float


# Properties to receive via API on update
class UmbralUpdate(UmbralBase):
    pass


class UmbralInDBBase(UmbralBase):
    id: Optional[int] = None
    resultados: Optional[List[Resultado]] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Umbral(UmbralInDBBase):
    pass
