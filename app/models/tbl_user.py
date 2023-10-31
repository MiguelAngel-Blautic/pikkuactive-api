from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_model import tbl_model  # noqa: F401


class tbl_user(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldBActive = Column(Boolean(), default=True)
    fldSDireccion = Column(String)
    fldSTelefono = Column(String)
    fldSEmail = Column(String)
    fldSHashedPassword = Column(String)
    fldSImagen = Column(String)
    idPlataforma = Column(Integer)
    fkRol = Column(ForeignKey('tbl_rol.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    rol = relationship("tbl_rol")
    models = relationship("tbl_model", back_populates="owner", cascade="all,delete", )


class tbl_rol(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)
