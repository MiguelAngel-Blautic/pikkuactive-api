from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class tbl_image_device(Base):
    id = Column(Integer, primary_key=True, index=True)
    fldSImage = Column(String)
    fkModel = Column(Integer)
    fkPosition = Column(Integer)
