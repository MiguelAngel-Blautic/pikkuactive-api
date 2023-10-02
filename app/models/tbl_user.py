from typing import TYPE_CHECKING

from mariadb.constants.FIELD_TYPE import DATE
from pymysql import Date, TIMESTAMP
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .tbl_model import tbl_model  # noqa: F401


class tbl_user(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSFullName = Column(String, index=True)
    fldSEmail = Column(String, unique=True, index=True, nullable=False)
    fldSHashedPassword = Column(String, nullable=False)
    fldBActive = Column(Boolean(), default=True)
    fldSTelefono = Column(String)
    fldSImagen = Column(String)
    fldTNacimiento = Column(TIMESTAMP)
    fldNSexo = Column(Integer)
    fkRol = Column(Integer)
    idPlataforma = Column(Integer)
    fldSFcmToken = Column(String, nullable=True)
    models = relationship("tbl_model", back_populates="owner", cascade="all,delete", )