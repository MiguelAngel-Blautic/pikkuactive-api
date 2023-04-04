from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class tbl_grupo_negativo(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldTNombre = Column(String(255), nullable=False)
    fldTDescripcion = Column(String)
    grupo = relationship("tbl_capture", back_populates="grupo", cascade="all,delete", single_parent=True)
