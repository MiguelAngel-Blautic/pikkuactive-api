from typing import Optional

from pydantic import BaseModel


class History(BaseModel):
    id: int
    fkCapture: int
    fkOwner: int

    class Config:
        orm_mode = True
