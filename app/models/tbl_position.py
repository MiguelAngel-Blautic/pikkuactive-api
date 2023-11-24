from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class tbl_position(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSName = Column(String(255), nullable=False)
    fldSDescription = Column(String)
    positions = relationship("tbl_device", back_populates="position", cascade="all,delete", single_parent=True)
    posiciones = relationship("tbl_dispositivo_sensor", back_populates="posicion", cascade="all,delete", single_parent=True)
