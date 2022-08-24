from datetime import date, datetime
from typing import List, Type

import DateTime.DateTime
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, not_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_asignado import tbl_asignado
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.models.tbl_entrena import tbl_entrena
from app.models.tbl_model import tbl_model, TrainingStatus
from app.models.tbl_plan import tbl_planes
from app.schemas import PlanCreate, PlanUpdate, EjercicioCreate, EjercicioUpdate, Plan, EjercicioResumen


class CRUDEjercicio(CRUDBase[tbl_ejercicio, EjercicioCreate, EjercicioUpdate]):

    def create_with_owner(
            self, db: Session, *, db_obj: tbl_planes, obj_in: EjercicioCreate,
    ) -> tbl_ejercicio:
        obj_in_data = obj_in.dict()
        umbrales_in_ej = obj_in_data.pop('umbrales', None)

        ejercicio = tbl_ejercicio(**obj_in_data, fkPlan=db_obj.id, plan=db_obj)
        db.add(ejercicio)
        db.commit()
        db.refresh(ejercicio)
        id_ejercicio = ejercicio.id
        for umbral in umbrales_in_ej:
            umbral.pop('resultados', None)
            umbral = tbl_umbrales(**umbral, fkEjercicio=id_ejercicio)
            db.add(umbral)
            db.commit()
            db.refresh(umbral)
        ejercicio = db.query(tbl_ejercicio).filter(tbl_ejercicio.id == id_ejercicio).first()
        return ejercicio

    def get_multi_by_rol(
            self, db: Session, *, user: int, rol: int, skip: int = 0, limit: int = 100, id: int,
    ) -> List[tbl_ejercicio]:
        if rol == 1:
            return db.query(tbl_ejercicio).outerjoin(tbl_planes, tbl_planes.id == tbl_ejercicio.fkPlan). \
                filter(tbl_ejercicio.fkPlan == id).outerjoin(tbl_asignado, tbl_planes.id == tbl_asignado.fkPlan). \
                filter(tbl_asignado.fkUsuario == user).offset(skip).limit(limit).all()
        if rol == 2:
            return db.query(tbl_ejercicio).outerjoin(tbl_planes, tbl_planes.id == tbl_ejercicio.fkPlan).filter(tbl_planes.fkCreador == user). \
                filter(tbl_ejercicio.fkPlan == id).offset(skip).limit(limit).all()
        if rol == 3:
            res = db.query(tbl_ejercicio).outerjoin(tbl_planes, tbl_planes.id == tbl_ejercicio.fkPlan).outerjoin(tbl_entrena,
                                                                                                                 tbl_planes.fkCreador == tbl_entrena.fkUsuario). \
                filter(or_(tbl_entrena.fkProfesional == user, tbl_planes.fkCreador == user)). \
                filter(tbl_ejercicio.fkPlan == id).offset(skip).limit(limit).all()
            return res
        if rol == 4:
            return db.query(self.model).filter(tbl_ejercicio.fkPlan == id).offset(skip).limit(limit).all()

    def readUser(
            self, *, db: Session, user: int,
    ) -> List[EjercicioResumen]:
        res = []
        current_time = date.today()
        ejercicios = db.query(tbl_ejercicio).join(tbl_asignado, tbl_ejercicio.fkPlan == tbl_asignado.fkPlan). \
            filter(tbl_asignado.fkUsuario == user).filter(not_(tbl_ejercicio.fldDDia < current_time)). \
            order_by(tbl_ejercicio.fldDDia).all()
        for ejercicio in ejercicios:
            modelo = db.query(tbl_model).filter(tbl_model.id == ejercicio.fkEjercicio).first()
            resultados = db.query(tbl_historico_valores).outerjoin(tbl_umbrales, tbl_historico_valores.fkUmbral == tbl_umbrales.id). \
                filter(tbl_umbrales.fkEjercicio == ejercicio.id).filter(tbl_umbrales.fldFValor <= tbl_historico_valores.fldFValor).all()
            obj = EjercicioResumen()
            obj.id = ejercicio.id
            obj.fkEjercicio = modelo.id
            obj.fldNRepeticiones = ejercicio.fldNRepeticiones
            obj.fldDDia = ejercicio.fldDDia
            obj.imagen = modelo.fldSImage
            obj.nombre = modelo.fldSName
            obj.progreso = len(resultados)
            res.append(obj)
        return res


ejercicio = CRUDEjercicio(tbl_ejercicio)
