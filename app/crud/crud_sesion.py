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
from app.schemas import SesionCreate, SesionUpdate, EjercicioCreate, EjercicioResumen, Sesion, User
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

    def getCompleta(
            self, db: Session, *, id: int,
    ) -> List[Sesion]:
        plan = sesion.get(db=db, id=id)
        res = []
        lista = db.query(tbl_asignado).filter(tbl_asignado.fkSesion == plan.id).all()
        for asign in lista:
            usr = db.query(tbl_user).filter(tbl_user.id == asign.fkUsuario).first()
            res.append(User(id=usr.id, fldBActive=usr.fldBActive, fldSDireccion=usr.fldSDireccion, fldSTelefono=usr.fldSTelefono, fldSImagen=usr.fldSImagen, fkRol=usr.fkRol))
        plan.usuarios = res
        return plan

    def get_multi_by_rol(
            self, db: Session, *, user: int, rol: int, skip: int = 0, limit: int = 100
    ) -> List[Sesion]:
        planes = []
        if rol == 0:
            planes = []
            asignados = db.query(tbl_asignado).filter(tbl_asignado.fkUsuario == user).offset(skip).limit(limit).all()
            for asignacion in asignados:
                planes.append(sesion.get(db=db, id=asignacion.fkSesion))
        if rol == 1:
            planes = db.query(self.model).filter(tbl_sesion.fkCreador == user).offset(skip).limit(limit).all()
            for i in range(len(planes)):
                planes[i] = Sesion(fldSNombre=planes[i].fldSNombre, fkCreador=planes[i].fkCreador, fldBGenerico=planes[i].fldBGenerico, id=planes[i].id, ejercicios=planes[i].ejercicios)
                asignados = db.query(tbl_asignado).filter(tbl_asignado.fkSesion == planes[i].id).offset(skip).limit(limit).all()
                for asignado in asignados:
                    usuario = db.query(tbl_user).get(asignado.fkUsuario)
                    if usuario:
                        planes[i].usuarios.append(usuario)
        return planes

    def get_multi_by_usr(
            self, db: Session, *, prof: int, user: int
    ) -> List[Sesion]:
        res = []
        planes = db.query(self.model).filter(tbl_sesion.fkCreador == prof).all()
        for plan in planes:
            cant = db.query(tbl_asignado).filter(tbl_asignado.fkSesion == plan.id).filter(tbl_asignado.fkUsuario == user).all()
            if len(cant) > 0:
                res.append(plan)
        return res



sesion = CRUDSesion(tbl_sesion)
