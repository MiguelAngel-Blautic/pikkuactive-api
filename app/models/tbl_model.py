import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_user  # noqa: F401


class TrainingStatus(enum.Enum):
    no_training = 0
    training_started = 1
    training_succeeded = 2
    training_failed = 3


class tbl_model(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSName = Column(String, index=True)
    fldSDescription = Column(String, index=True)
    fldNDuration = Column(Integer, nullable=False)
    fldDTimeCreateTime = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    fldBAutoTraining = Column(Boolean())
    fldSImage = Column(String)
    fldSVideo = Column(String)
    fldSStatus = Column(Enum(TrainingStatus))
    fldNProgress = Column(Integer)

    fkOwner = Column(Integer, ForeignKey("tbl_user.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("tbl_user", back_populates="models")
    fkCreador = Column(Integer)
    fkTipo = Column(Integer, ForeignKey("tbl_tipo_modelo.id", ondelete="CASCADE", onupdate="CASCADE"))
    tipo = relationship("tbl_tipo_modelo")

    movements = relationship("tbl_movement", back_populates="owner", cascade="all,delete", single_parent=True)
    devices = relationship("tbl_device", back_populates="owner", cascade="all,delete", single_parent=True)
    versions = relationship("tbl_version", back_populates="owner", cascade="all,delete", single_parent=True, order_by="tbl_version.fldDTimeCreateTime")


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


class tbl_pertenece(Base):
    fkUsuario = Column(Integer, primary_key=True)
    fkModel = Column(Integer, primary_key=True)
    fkAsignado = Column(Integer)
    fldBPermiso = Column(Boolean)