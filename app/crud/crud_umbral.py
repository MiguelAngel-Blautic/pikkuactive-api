from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.schemas import PlanCreate, PlanUpdate, EjercicioCreate, EjercicioUpdate, Plan, UmbralUpdate, UmbralCreate


class CRUDUmbral(CRUDBase[tbl_umbrales, UmbralCreate, UmbralUpdate]):

    def create_with_owner(
            self, db: Session, *, db_obj: tbl_ejercicio, obj_in: UmbralCreate,
    ) -> tbl_umbrales:
        obj_in_data = obj_in.dict()

        umbral = tbl_umbrales(**obj_in_data, fkEjercicio=db_obj.id, ejercicio=db_obj)
        db.add(umbral)
        db.commit()
        db.refresh(umbral)
        id_umbral = umbral.id
        umbral = db.query(tbl_umbrales).filter(tbl_umbrales.id == id_umbral).first()
        return umbral

    def get_multi_valores(
            self, db: Session, *, ejercicio: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_umbrales]:
        return db.query(tbl_umbrales).filter(tbl_umbrales.fkEjercicio == ejercicio).offset(skip).limit(limit).all()


umbral = CRUDUmbral(tbl_umbrales)
