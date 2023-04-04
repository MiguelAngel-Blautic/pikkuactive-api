from typing import Optional

from pydantic import BaseModel


# Shared properties
class GrupoBase(BaseModel):
    fldTNombre: Optional[str] = None
    fldTDescripcion: Optional[str] = None


# Properties to receive on position creation
class GrupoCreate(GrupoBase):
    fldTNombre: str


# Properties to receive on position update
class GrupoUpdate(GrupoBase):
    pass


# Properties shared by position stored in DB
class GrupoInDBBase(GrupoBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Grupo(GrupoInDBBase):
    pass


# Properties properties stored in DB
class GrupoInDB(GrupoInDBBase):
    pass
