from sqlalchemy import Column, Integer, String

from app.db.base_class import Base


class Position(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String)
