from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_position import tbl_position  # noqa: F401
    from .tbl_model import tbl_model  # noqa: F401


class tbl_tipo_sensor(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)
    fldNFrecuencia = Column(Integer)
    fldNValores = Column(Integer)
    sensores = relationship("tbl_dispositivo_sensor", back_populates="sensor", cascade="all,delete", single_parent=True)


class tbl_dispositivo_sensor(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkPosicion = Column(Integer, ForeignKey("tbl_position.id", ondelete="CASCADE", onupdate="CASCADE"))
    posicion = relationship("tbl_position", back_populates="posiciones")
    fkOwner = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("tbl_model", back_populates="dispositivos")
    fkSensor = Column(Integer, ForeignKey("tbl_tipo_sensor.id", ondelete="CASCADE", onupdate="CASCADE"))
    sensor = relationship("tbl_tipo_sensor", back_populates="sensores")
    datos = relationship("tbl_dato", back_populates="dispositivoSensor", cascade="all,delete", single_parent=True)


class tbl_dato(Base):
    fldNSample = Column(Integer, primary_key=True)
    fldFValor = Column(Float)
    fldFValor2 = Column(Float, nullable=True)
    fldFValor3 = Column(Float, nullable=True)
    fkDispositivoSensor = Column(Integer, ForeignKey("tbl_dispositivo_sensor.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    dispositivoSensor = relationship("tbl_dispositivo_sensor", back_populates="datos")
    fkCaptura = Column(Integer, ForeignKey("tbl_capture.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    captura = relationship("tbl_capture", single_parent=True)
