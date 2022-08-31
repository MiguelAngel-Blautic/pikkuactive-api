import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_user  # noqa: F401


class tbl_entrena(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkUsuario = Column(Integer)
    fkProfesional = Column(Integer)
    fldBConfirmed = Column(Integer)