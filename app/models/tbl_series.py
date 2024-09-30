from sqlalchemy import Column, Integer, String
from app.db.base_class import Base


class tbl_series(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSDescripcion = Column(String)
    fkBloque = Column(Integer)
    fldNRepeticiones = Column(Integer)
    fldNDescanso = Column(Integer)
    fldNOrden = Column(Integer)
    fkCreador = Column(Integer)
    fkPadre = Column(Integer)
    fldBSimultanea = Column(Integer)
