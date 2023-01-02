from typing import Optional, List
from pydantic import BaseModel


# Aditional Class
# Ecg
class EcgBase(BaseModel):
    fldNSample: int
    fldNTime: int
    fldFData0: float
    fldFData1: float
    fldFData2: float
    fldFData3: float
    fldSType: Optional[str] = None


class EcgCreate(EcgBase):
    fldNSample: int
    fldNTime: int
    fldFData0: float
    fldFData1: float
    fldFData2: float
    fldFData3: float
    fldSType: Optional[str] = None
    fkDevice: int


# Properties shared by movement stored in DB
class EcgInDBBase(EcgBase):
    fkOwner: int
    fkDevice: int

    class Config:
        orm_mode = True


class Ecg(EcgInDBBase):
    class Config:
        orm_mode = True
