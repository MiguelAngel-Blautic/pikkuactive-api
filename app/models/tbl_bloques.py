from sqlalchemy import Column, Integer, String
from app.db.base_class import Base


class tbl_bloques(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSDescripcion = Column(String)
    fkEntrenamiento = Column(Integer)
    fldNDescanso = Column(Integer)
    fldNOrden = Column(Integer)
    fkCreador = Column(Integer)
