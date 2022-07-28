from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_model  # noqa: F401


class tbl_movement(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSLabel = Column(String(45), nullable=False)
    fldSDescription = Column(String, index=True)
    fldDTimeCreateTime = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    fkOwner = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("tbl_model", back_populates="movements")
