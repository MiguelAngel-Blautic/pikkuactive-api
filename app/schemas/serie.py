from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class SerieBase(BaseModel):
    fldSDescripcion: str
    fldNDescanso: int
    fldNRepeticiones: int


# Properties to receive via API on creation
class SerieCreate(SerieBase):
    fkBloque: int
    pass


class SerieUpdate(SerieBase):
    pass


class Serie(SerieBase):
    fkBloque: int
    fldNOrden: int
    id: int
    class Config:
        orm_mode = True
