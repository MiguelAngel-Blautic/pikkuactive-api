import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401


class TrainingStatus(enum.Enum):
    no_training = 0
    training_started = 1
    training_succeeded = 2
    training_failed = 3


class Model(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    duration = Column(Integer, nullable=False)
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    auto_training = Column(Boolean())
    image = Column(String)
    video = Column(String)
    status = Column(Enum(TrainingStatus))
    progress = Column(Integer)

    owner_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("User", back_populates="models")

    movements = relationship("Movement", back_populates="owner", cascade="all,delete", single_parent=True)
    devices = relationship("Device", back_populates="owner", cascade="all,delete", single_parent=True)
    versions = relationship("Version", back_populates="owner", cascade="all,delete", single_parent=True, order_by="Version.create_time")


class Version(Base):
    id = Column(Integer, primary_key=True)
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    accuracy = Column(Float)
    epoch = Column(Integer)
    loss = Column(Float)
    optimizer = Column(String)
    learning_rate = Column(Float)
    url = Column(String)

    owner_id = Column(Integer, ForeignKey("model.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("Model",  single_parent=True)
    history = relationship("History", back_populates="owner", cascade="all,delete", single_parent=True)


class History(Base):
    id = Column(Integer, primary_key=True)
    id_capture = Column(Integer, ForeignKey("capture.id"))

    owner_id = Column(Integer, ForeignKey("version.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("Version", single_parent=True)
