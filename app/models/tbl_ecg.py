from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class tbl_ecg(Base):
    fldNSample = Column(Integer, nullable=False, primary_key=True)
    fldNTime = Column(Integer, nullable=False)
    fldFData = Column(Float, nullable=False)
    fldSType = Column(String, nullable=True)

    fkDevice = Column(ForeignKey('tbl_device.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True, primary_key=True)
    device = relationship("tbl_device")

    fkOwner = Column(Integer, ForeignKey("tbl_capture.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, primary_key=True)
    owner = relationship("tbl_capture", single_parent=True)

