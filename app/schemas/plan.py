from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class PlanBase(BaseModel):
    fldSNombre: str


# Properties to receive via API on creation
class PlanCreate(PlanBase):
    fkCliente: int


class PlanUpdate(PlanBase):
    pass


class Plan(PlanBase):
    fkCreador: int
    fkCliente: int
    id: int
    class Config:
        orm_mode = True
