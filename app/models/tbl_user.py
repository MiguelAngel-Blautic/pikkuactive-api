from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_model import tbl_model  # noqa: F401


class tbl_user(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSFullName = Column(String, index=True)
    fldSEmail = Column(String, unique=True, index=True, nullable=False)
    fldSHashedPassword = Column(String, nullable=False)
    fldBActive = Column(Boolean(), default=True)
    fkRol = Column(ForeignKey('tbl_rol.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True, primary_key=True)
    rol = relationship("tbl_rol")
    fldSFcmToken = Column(String, nullable=True)
    models = relationship("tbl_model", back_populates="owner", cascade="all,delete", )


class tbl_rol(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)
