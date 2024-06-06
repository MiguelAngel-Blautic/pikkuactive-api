from sqlalchemy import Column, Integer, Float, String, DateTime
from app.db.base_class import Base


class tbl_tipo_datos(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldFNombre = Column(String)


class tbl_registro_ejercicios(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkEjercicio = Column(Integer)
    fkTipoDato = Column(Integer)


class tbl_resultados(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkRegistro = Column(Integer)
    fldFValor = Column(Float)
    fldDTime = Column(DateTime)