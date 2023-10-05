import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum, BIGINT
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_user  # noqa: F401


class TrainingStatus(enum.Enum):
    no_training = 0
    training_started = 1
    training_succeeded = 2
    training_failed = 3


class tbl_categorias(Base):
    id = Column(BIGINT, primary_key=True, index=True)
    fldSNombre = Column(String)
    models = relationship("tbl_model", back_populates="categoria" )


class tbl_model(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSName = Column(String, index=True)
    fldSDescription = Column(String, index=True)
    fldNDuration = Column(Integer, nullable=False)
    fldDTimeCreateTime = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    fldSImage = Column(String)
    fldSVideo = Column(String)
    fldSStatus = Column(Enum(TrainingStatus))
    fldNProgress = Column(Integer)
    fldBPublico = Column(Integer)
    fkCategoria = Column(Integer, ForeignKey("tbl_categorias.id", ondelete="SET_NULL", onupdate="SET_NULL"))
    categoria = relationship("tbl_categorias", back_populates="models")
    fldFPrecio = Column(Float)

    fkOwner = Column(Integer, ForeignKey("tbl_user.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("tbl_user", back_populates="models")
    fkTipo = Column(Integer, ForeignKey("tbl_tipo_modelo.id", ondelete="CASCADE", onupdate="CASCADE"))
    tipo = relationship("tbl_tipo_modelo")

    movements = relationship("tbl_movement", back_populates="owner", cascade="all,delete", single_parent=True)
    devices = relationship("tbl_device", back_populates="owner", cascade="all,delete", single_parent=True)
    versions = relationship("tbl_version", back_populates="owner", cascade="all,delete", single_parent=True, order_by="tbl_version.fldDTimeCreateTime")
    versionsEst = relationship("tbl_version_estadistica", back_populates="owner", cascade="all,delete", single_parent=True, order_by="tbl_version_estadistica.fecha")
    sensoresEst = relationship("sensores_estadistica", back_populates="owner", cascade="all,delete", single_parent=True, order_by="sensores_estadistica.fldNOrden")


class tbl_compra_modelo(Base):
    fkModelo = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    fkUsuario = Column(Integer, ForeignKey("tbl_user.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    fldDFecha = Column(TIMESTAMP)


class tbl_version(Base):
    id = Column(Integer, primary_key=True)
    fldDTimeCreateTime = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    fldFAccuracy = Column(Float)
    fldNEpoch = Column(Integer)
    fldFLoss = Column(Float)
    fldSOptimizer = Column(String)
    fldFLearningRate = Column(Float)
    fldSUrl = Column(String)

    fkOwner = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("tbl_model",  single_parent=True)
    history = relationship("tbl_history", back_populates="owner", cascade="all,delete", single_parent=True)


class tbl_history(Base):
    id = Column(Integer, primary_key=True)
    fkCapture = Column(Integer, ForeignKey("tbl_capture.id"))

    fkOwner = Column(Integer, ForeignKey("tbl_version.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("tbl_version", single_parent=True)


class tbl_tipo_modelo(Base):
    id = Column(Integer, primary_key=True)
    fkSNombre = Column(Integer)