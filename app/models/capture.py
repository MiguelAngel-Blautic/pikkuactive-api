from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .movement import Movement  # noqa: F401


class Capture(Base):
    id = Column(Integer, primary_key=True, index=True)
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    owner_id = Column(Integer, ForeignKey("movement.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("Movement")

    mpu = relationship("Mpu", back_populates="owner", cascade="all,delete", order_by="Mpu.sample")
    ecg = relationship("Ecg", back_populates="owner", cascade="all,delete", order_by="Ecg.sample")

