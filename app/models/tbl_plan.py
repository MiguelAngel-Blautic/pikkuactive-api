import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_user  # noqa: F401


class tbl_planes(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String, index=True)
    fldBGenerico = Column(Boolean())

    fkCreador = Column(Integer, ForeignKey("tbl_user.id", ondelete="CASCADE", onupdate="CASCADE"))
    creador = relationship("tbl_user")

    ejercicios = relationship("tbl_ejercicio", back_populates="plan", cascade="all,delete", single_parent=True)
