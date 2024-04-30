from sqlalchemy import Column, Integer, TIMESTAMP, String
from app.db.base_class import Base

class tbl_entrenamientos(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldDDia = Column(TIMESTAMP, nullable=True)
    fkCreador = Column(Integer)
    fkPlan = Column(Integer, nullable=True)
    fldSNombre = Column(String, nullable=True)
    fkPadre = Column(Integer, nullable=True)
