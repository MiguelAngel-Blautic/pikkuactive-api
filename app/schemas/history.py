from typing import Optional

from pydantic import BaseModel


class History(BaseModel):
    id: int
    id_capture: int
    owner_id: int

    class Config:
        orm_mode = True
