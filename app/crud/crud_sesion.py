from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, false
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement, tbl_user
from app.models.tbl_asignado import tbl_asignado
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales
from app.models.tbl_entrena import tbl_entrena
from app.models.tbl_model import tbl_model, TrainingStatus
from app.models.tbl_sesion import tbl_sesion
from app.schemas import SesionCreate, SesionUpdate, EjercicioCreate, EjercicioResumen, Sesion
from app.schemas.sesion import SesionExtended


class CRUDSesion(CRUDBase[tbl_sesion, SesionCreate, SesionUpdate]):

    def create_with_owner(
            self, db: Session, *, obj_in: SesionCreate,
    ) -> tbl_sesion:
        obj_in_data = obj_in.dict()

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_rol(
            self, db: Session, *, user: int, rol: int, skip: int = 0, limit: int = 100
    ) -> List[Sesion]:
        global planes
        if rol == 1:
            return []
        if rol == 2 or rol == 3:
            planes = db.query(self.model).filter(tbl_sesion.fkCreador == user).offset(skip).limit(limit).all()
        if rol == 4:
            planes = db.query(self.model).offset(skip).limit(limit).all()

        return planes



sesion = CRUDSesion(tbl_sesion)
