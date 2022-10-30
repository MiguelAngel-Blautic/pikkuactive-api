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
from app.schemas import SesionCreate, SesionUpdate, EjercicioCreate, EjercicioResumen

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
    ) -> List[PlanResumen]:
        global planes
        resultado = []
        if rol == 1:
            return []
        if rol == 2:
            planes = db.query(self.model).filter(tbl_sesion.fkCreador == user).filter(tbl_sesion.fldBGenerico == None).offset(skip).limit(limit).all()
        if rol == 3:
            planes = db.query(tbl_sesion).outerjoin(tbl_entrena, tbl_sesion.fkCreador == tbl_entrena.fkUsuario). \
                filter(or_(tbl_entrena.fkProfesional == user, tbl_sesion.fkCreador == user)). \
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



sesion = CRUDSesion(tbl_sesion)
