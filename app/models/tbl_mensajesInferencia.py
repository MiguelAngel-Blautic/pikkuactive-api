from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class tbl_mensajesInferencia(Base):
    __tablename__ = "tbl_mensajesInferencia"
    fldNDevice = Column(Integer, nullable=False, primary_key=True)
    fldNSensor = Column(Integer, nullable=False, primary_key=True)
    fldNEje = Column(Integer, nullable=False, primary_key=True)
    fldNIntensidad = Column(Integer, nullable=False, primary_key=True)
    fldSMensaje = Column(String)

