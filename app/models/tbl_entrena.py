from sqlalchemy import Column, Integer
from app.db.base_class import Base


class tbl_entrena(Base):
    id = Column(Integer, primary_key=True, index=True)
    fkUsuario = Column(Integer)
    fkProfesional = Column(Integer)
    fldBConfirmed = Column(Integer)