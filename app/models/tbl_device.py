from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_position import tbl_position  # noqa: F401
    from .tbl_model import tbl_model  # noqa: F401


class tbl_device(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldNNumberDevice = Column(Integer, nullable=False)
    fkPosition = Column(Integer, ForeignKey("tbl_position.id", ondelete="CASCADE", onupdate="CASCADE"))
    position = relationship("tbl_position", back_populates="positions")

    fkOwner = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("tbl_model", back_populates="devices")
