from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Ecg(Base):
    sample = Column(Integer, nullable=False, primary_key=True)
    time = Column(Integer, nullable=False)
    data = Column(Float, nullable=False)
    type = Column(String, nullable=True)

    device_id = Column(ForeignKey('device.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True, primary_key=True)
    device = relationship("Device")

    owner_id = Column(Integer, ForeignKey("capture.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, primary_key=True)
    owner = relationship("Capture", single_parent=True)

