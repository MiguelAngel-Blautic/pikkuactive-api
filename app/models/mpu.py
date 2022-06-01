from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .capture import Capture  # noqa: F401


class Mpu(Base):
    sample = Column(Integer, nullable=False, primary_key=True)
    acc_x = Column(Float, nullable=False)
    acc_y = Column(Float, nullable=False)
    acc_z = Column(Float, nullable=False)
    gyr_x = Column(Float, nullable=False)
    gyr_y = Column(Float, nullable=False)
    gyr_z = Column(Float, nullable=False)

    device_id = Column(ForeignKey('device.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True, primary_key=True)
    device = relationship("Device")

    owner_id = Column(Integer, ForeignKey("capture.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, primary_key=True)
    owner = relationship("Capture", single_parent=True)

