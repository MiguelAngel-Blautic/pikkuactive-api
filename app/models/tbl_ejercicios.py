from sqlalchemy import Column, Integer, Float, DateTime, String
from app.db.base_class import Base


class tbl_dato(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkSensor = Column(Integer)
    fkSesion = Column(Integer)
    fldDTime = Column(DateTime)
    fldFValor = Column(Float)

class tbl_sensores(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)
    fldNMin = Column(Float)
    fldNMax = Column(Float)
    fldNFrec = Column(Integer)


class tbl_sesion(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldDInicio = Column(DateTime)
    fldNEdad = Column(Integer)
    fldFAltura = Column(Integer)
    fldFPeso = Column(Float)
    fldNSexo = Column(Integer)


class tbl_marcas(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldNTipo = Column(Integer)
    fldNValor = Column(Integer)
    fldDTime = Column(DateTime)
    fkSesion = Column(Integer)