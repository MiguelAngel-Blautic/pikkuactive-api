from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import Model  # noqa: F401


class Movement(Base):
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(45), nullable=False)
    description = Column(String, index=True)
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    owner_id = Column(Integer, ForeignKey("model.id", ondelete="CASCADE", onupdate="CASCADE"))
    owner = relationship("Model", back_populates="movements")
