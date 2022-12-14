from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_movement import tbl_movement  # noqa: F401


class tbl_capture(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldDTimeCreateTime = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    fkOwner = Column(Integer, ForeignKey("tbl_movement.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("tbl_movement")

    mpu = relationship("tbl_mpu", back_populates="owner", cascade="all,delete", order_by="tbl_mpu.fldNSample")
    ecg = relationship("tbl_ecg", back_populates="owner", cascade="all,delete", order_by="tbl_ecg.fldNSample")

