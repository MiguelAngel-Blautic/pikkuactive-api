from sqlalchemy import Column, Integer, Float, String
from app.db.base_class import Base


class tbl_ejercicios(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkSerie = Column(Integer)
    fldNDescanso = Column(Integer)
    fldNDuracion = Column(Integer, nullable=True)
    fldNDuracionEfectiva = Column(Integer, nullable=True)
    fldNRepeticiones = Column(Integer, nullable=True)
    fldFVelocidad = Column(Float, nullable=True)
    fldFUmbral = Column(Float, nullable=True)
    fldNOrden = Column(Integer)
    fkModelo = Column(Integer, nullable=True)
    fkCreador = Column(Integer)
    fldSToken = Column(String)
