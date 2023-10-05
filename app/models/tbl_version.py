import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum, BIGINT
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_user  # noqa: F401


class tbl_version_estadistica(Base):
    id = Column(Integer, primary_key=True)
    fecha = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    accuracy = Column(Float)
    fldSLabel = Column(String)

    fkOwner = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("tbl_model",  single_parent=True)


class sensores_estadistica(Base):
    id = Column(Integer, primary_key=True)
    fldSNombre = Column(String)
    fldNOrden = Column(Integer)
    fkModelo = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("tbl_model", single_parent=True)
    fldFMax = Column(Float)
    fldFMin = Column(Float)


class datos_estadistica(Base):
    fkSensor = Column(Integer, nullable=False, primary_key=True)
    fkVersion = Column(Integer, nullable=False, primary_key=True)
    fldNSample = Column(Integer, primary_key=True)
    fldFStd = Column(Float)
    fldFMedia = Column(Float)

