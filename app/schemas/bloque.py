from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class BloqueBase(BaseModel):
    fldSDescripcion: str
    fldNDescanso: int


# Properties to receive via API on creation
class BloqueCreate(BloqueBase):
    fkEntrenamiento: int
    pass


class BloqueUpdate(BloqueBase):
    pass


class Bloque(BloqueBase):
    fkEntrenamiento: int
    fldNOrden: int
    id: int
    class Config:
        orm_mode = True
