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
from app.models.tbl_plan import tbl_planes
from app.schemas import PlanCreate, PlanUpdate, EjercicioCreate, EjercicioResumen
from app.schemas.plan import PlanResumen


class CRUDPlan(CRUDBase[tbl_planes, PlanCreate, PlanUpdate]):

    def create_with_owner(
            self, db: Session, *, obj_in: PlanCreate,
    ) -> tbl_planes:
        obj_in_data = obj_in.dict()

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_ejercicio(
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
            self, db: Session, *, user: int, rol: int, skip: int = 0, limit: int = 100
    ) -> List[PlanResumen]:
        global planes
        resultado = []
        if rol == 1:
            return []
        if rol == 2:
            planes = db.query(self.model).filter(tbl_planes.fkCreador == user).filter(tbl_planes.fldBGenerico == None).offset(skip).limit(limit).all()
        if rol == 3:
            planes = db.query(tbl_planes).outerjoin(tbl_entrena, tbl_planes.fkCreador == tbl_entrena.fkUsuario). \
                filter(or_(tbl_entrena.fkProfesional == user, tbl_planes.fkCreador == user)). \
                offset(skip).limit(limit).all()
        if rol == 4:
            planes = db.query(self.model).offset(skip).limit(limit).all()

        for plan in planes:
            print(plan.fldBGenerico)
            obj = PlanResumen()
            obj.fldSNombre = plan.fldSNombre
            obj.id = plan.id
            obj.ejercicios = []
            for ejercicio in plan.ejercicios:
                modelo = db.query(tbl_model).filter(tbl_model.id == ejercicio.fkEjercicio).first()
                aux = EjercicioResumen()
                aux.id = ejercicio.id
                aux.fkEjercicio = modelo.id
                aux.fldNRepeticiones = ejercicio.fldNRepeticiones
                aux.fldDDia = ejercicio.fldDDia
                aux.imagen = modelo.fldSImage
                aux.nombre = modelo.fldSName
                if len(ejercicio.umbrales) > 0:
                    aux.fkUmbral = ejercicio.umbrales[0].id
                    aux.umbral = ejercicio.umbrales[0].fldFValor
                else:
                    aux.umbral = 50
                obj.ejercicios.append(aux)
            resultado.append(obj)
        return resultado

    def get_pendientes(
            self, db: Session, *, user: int
    ) -> List[PlanResumen]:
        global planes
        resultado = []
        planes = db.query(self.model).filter(tbl_planes.fkCreador == user).all()

        for plan in planes:
            print(plan.fldBGenerico)
            obj = PlanResumen()
            obj.fldSNombre = plan.fldSNombre
            obj.id = plan.id
            obj.ejercicios = []
            for ejercicio in plan.ejercicios:
                modelo = db.query(tbl_model).filter(tbl_model.id == ejercicio.fkEjercicio).first()
                aux = EjercicioResumen()
                aux.id = ejercicio.id
                aux.fkEjercicio = modelo.id
                aux.fldNRepeticiones = ejercicio.fldNRepeticiones
                aux.fldDDia = ejercicio.fldDDia
                aux.imagen = modelo.fldSImage
                aux.nombre = modelo.fldSName
                if len(ejercicio.umbrales) > 0:
                    aux.fkUmbral = ejercicio.umbrales[0].id
                    aux.umbral = ejercicio.umbrales[0].fldFValor
                else:
                    aux.umbral = 50
                obj.ejercicios.append(aux)
            resultado.append(obj)
        return resultado

    def asignar_plan(
            self, db: Session, *, paciente: int, plan: int, user: tbl_user
    ) -> tbl_asignado:
        plan = tbl_asignado(fkUsuario=paciente, fkAsignador=user.id, fkPlan=plan)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def desasignar_plan(
            self, db: Session, *, paciente: int, plan: int, user: tbl_user
    ) -> tbl_asignado:
        db.delete(tbl_asignado).where(tbl_asignado.fkUsuario == paciente).where(tbl_asignado.fkPlan == plan)
        db.commit()
        return plan


plan = CRUDPlan(tbl_planes)
