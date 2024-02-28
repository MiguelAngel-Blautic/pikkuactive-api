from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class tbl_notificaciones(Base):
    id = Column(Integer, nullable=False, primary_key=True, index=True)
    fldSTexto = Column(String, nullable=False)
    fldSVersionInclude = Column(String)
    fldSVersionExclude = Column(String)
    fldNUserInclude = Column(Integer)
    fldNUserExclude = Column(Integer)

