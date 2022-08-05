from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# Shared properties
from app.schemas.ejercicio import Ejercicio


class EntrenaBase(BaseModel):
    fkUsuario: Optional[int] = None
    fkProfesional: Optional[int] = None


# Properties to receive via API on creation
class EntrenaCreate(EntrenaBase):
    fkUsuario: int
    fkProfesional: int


# Properties to receive via API on update
class EntrenaUpdate(EntrenaBase):
    fldBConfirmed: Optional[bool] = None
    pass


class EntrenaInDBBase(EntrenaBase):
    id: Optional[int] = None
    fldBConfirmed: Optional[bool] = None

    class Config:
        orm_mode = True


# Properties to return to client
class Entrena(EntrenaInDBBase):
    pass
