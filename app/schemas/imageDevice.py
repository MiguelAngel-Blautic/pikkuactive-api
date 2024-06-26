from tokenize import String
from typing import Optional

from pydantic import BaseModel
from app.schemas.position import Position


# Shared properties
class ImageDevice(BaseModel):
    fkModel: int
    fkPosition: int
    fldSImage: str
