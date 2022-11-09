from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class tbl_position(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSName = Column(String(255), nullable=False)
    fldSDescription = Column(String)
