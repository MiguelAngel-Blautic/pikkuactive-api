from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    rol: int
    id: int
    fullName: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None
