from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.schemas import PlanCreate, PlanUpdate, EjercicioCreate, EjercicioUpdate, Plan, UmbralUpdate, UmbralCreate, ResultadoCreate, ResultadoUpdate


class CRUDResultado(CRUDBase[tbl_historico_valores, ResultadoCreate, ResultadoUpdate]):

    def create_with_owner(
            self, db: Session, *, db_obj: tbl_umbrales, obj_in: ResultadoCreate,
    ) -> tbl_historico_valores:
        obj_in_data = obj_in.dict()

        resultado = tbl_historico_valores(**obj_in_data, fkUmbral=db_obj.id, umbral=db_obj)
        db.add(resultado)
        db.commit()
        db.refresh(resultado)
        return resultado

    def get_multi_valores(
            self, db: Session, *, umbral: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_historico_valores]:
        return db.query(tbl_historico_valores).filter(tbl_historico_valores.fkUmbral == umbral).offset(skip).limit(limit).all()


resultado = CRUDResultado(tbl_historico_valores)
