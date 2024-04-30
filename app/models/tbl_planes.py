from sqlalchemy import Column, Integer, String
from app.db.base_class import Base


class tbl_planes(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)
    fkCreador = Column(Integer)
    fkCliente = Column(Integer)
