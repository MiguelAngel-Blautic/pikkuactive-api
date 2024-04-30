from sqlalchemy import Column, Integer, String
from app.db.base_class import Base


class tbl_user(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSFullName = Column(String)
    fldSEmail = Column(String)
    fldSHashedPassword = Column(String, nullable=True)
    fldSDireccion = Column(String, nullable=True)
    fldSTelefono = Column(String, nullable=True)
    fldSImagen = Column(String, nullable=True)
    idPlataforma = Column(Integer)
    fkRol = Column(Integer)


class tbl_rol(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)