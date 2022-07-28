from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_capture import tbl_capture  # noqa: F401


class tbl_mpu(Base):
    fldNSample = Column(Integer, nullable=False, primary_key=True)
    fldFAccX = Column(Float, nullable=False)
    fldFAccY = Column(Float, nullable=False)
    fldFAccZ = Column(Float, nullable=False)
    fldFGyrX = Column(Float, nullable=False)
    fldFGyrY = Column(Float, nullable=False)
    fldFGyrZ = Column(Float, nullable=False)

    fkDevice = Column(ForeignKey('tbl_device.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True, primary_key=True)
    device = relationship("tbl_device")

    fkOwner = Column(Integer, ForeignKey("tbl_capture.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, primary_key=True)
    owner = relationship("tbl_capture", single_parent=True)

