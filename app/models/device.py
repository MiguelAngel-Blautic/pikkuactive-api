from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .position import Position  # noqa: F401
    from .model import Model  # noqa: F401


class Device(Base):
    id = Column(Integer, primary_key=True, index=True)
    number_device = Column(Integer, nullable=False)
    position_id = Column(Integer, ForeignKey('position.id'))
    position = relationship("Position")

    owner_id = Column(Integer, ForeignKey("model.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("Model", back_populates="devices")
