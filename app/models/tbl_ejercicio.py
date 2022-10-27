import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, Boolean, TIMESTAMP, Float, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_user import tbl_user  # noqa: F401


class tbl_ejercicio(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldDDia = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    fldNRepeticiones = Column(Integer)

    fkEjercicio = Column(Integer, ForeignKey("tbl_model.id", ondelete="CASCADE", onupdate="CASCADE"))
    ejercicio = relationship("tbl_model")
    fkSesion = Column(Integer, ForeignKey("tbl_sesion.id", ondelete="CASCADE", onupdate="CASCADE"))
    sesion = relationship("tbl_sesion")

    umbrales = relationship("tbl_umbrales", back_populates="ejercicio", cascade="all,delete", single_parent=True)


class tbl_umbrales(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldFValor = Column(Float)
    fkEjercicio = Column(Integer, ForeignKey("tbl_ejercicio.id", ondelete="CASCADE", onupdate="CASCADE"))
    ejercicio = relationship("tbl_ejercicio")
    fkTipo = Column(Integer, ForeignKey("tbl_tipo_umbral.id", ondelete="CASCADE", onupdate="CASCADE"))
    tipo = relationship("tbl_tipo_umbral")

    resultados = relationship("tbl_historico_valores", back_populates="umbral", cascade="all,delete", single_parent=True)


class tbl_tipo_umbral(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSNombre = Column(String)


class tbl_historico_valores(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldFValor = Column(Float)
    fldNIntento = Column(Integer)
    fldDTimeFecha = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    fldFUmbral = Column(Float)
    fkUmbral = Column(Integer, ForeignKey("tbl_umbrales.id", ondelete="CASCADE", onupdate="CASCADE"))
    umbral = relationship("tbl_umbrales")
