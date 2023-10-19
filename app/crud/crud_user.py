from datetime import date, datetime
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.tbl_asignado import tbl_asignado
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.models.tbl_entrena import tbl_entrena
from app.models.tbl_user import tbl_user
from app.schemas.user import UserCreate, UserUpdate, User


class CRUDUser(CRUDBase[tbl_user, UserCreate, UserUpdate]):

    def get_centros(self, db: Session, *, user: int, skip: int = 0, limit: int = 100) -> Optional[List[User]]:
        centros = db.query(tbl_user).filter(tbl_user.fkRol == 1).offset(skip).limit(limit).all()
        res = []
        for centro in centros:
            obj = User()
            obj.id = centro.id
            obj.fldBActive = centro.fldBActive
            obj.fldSDireccion = centro.fldSDireccion
            obj.fldSTelefono = centro.fldSTelefono
            obj.fldSImagen = centro.fldSImagen
            obj.fkRol = centro.fkRol
            obj.idPlataforma = centro.idPlataforma
            aux = db.query(tbl_entrena).filter(tbl_entrena.fkUsuario == user).filter(tbl_entrena.fkProfesional == centro.id).first()
            if aux:
                obj.idRelacion = aux.id
                obj.estado = aux.fldBConfirmed
            else:
                obj.estado = 0
            res.append(obj)
        return res

    def get_clientes(self, db: Session, *, user: int, rol: int) -> Optional[List[User]]:
        clientes = []
        res = []
        if rol == 1:
            clientes = db.query(tbl_user).outerjoin(tbl_entrena, tbl_user.id == tbl_entrena.fkUsuario).filter(tbl_entrena.fkProfesional == user).filter(tbl_entrena.fldBConfirmed).all()
        else:
            clientes = db.query(tbl_user).outerjoin(tbl_entrena, tbl_user.id == tbl_entrena.fkProfesional).filter(tbl_entrena.fkUsuario == user).all()

        for cliente in clientes:
            obj = User()
            obj.id = cliente.id
            obj.fldBActive = cliente.fldBActive
            obj.fldSDireccion = cliente.fldSDireccion
            obj.fldSTelefono = cliente.fldSTelefono
            obj.fldSImagen = cliente.fldSImagen
            obj.fkRol = cliente.fkRol
            obj.idPlataforma = cliente.idPlataforma
            aux = db.query(tbl_entrena).filter(tbl_entrena.fkUsuario == obj.id).filter(tbl_entrena.fkProfesional == user).first()
            if aux:
                obj.idRelacion = aux.id
                obj.estado = aux.fldBConfirmed
            else:
                obj.estado = 0
            res.append(obj)
        return res

    def get_profesionales(self, db: Session, *, skip: int = 0, limit: int = 100, user: tbl_user) -> Optional[List[tbl_user]]:
        if user.fkRol == 1:
            return db.query(tbl_user).outerjoin(tbl_entrena, tbl_entrena.fkUsuario == tbl_user.id).filter(tbl_user.fkRol == 2). \
                filter(tbl_entrena.fkProfesional == user.id).offset(skip).limit(limit).all()

    def get_pacientes(self, db: Session, *, skip: int = 0, limit: int = 100, user: tbl_user) -> Optional[List[tbl_user]]:
        if user.fkRol == 1:
            return db.query(tbl_user).outerjoin(tbl_entrena, tbl_entrena.fkUsuario == tbl_user.id).filter(tbl_user.fkRol == 1). \
                filter(tbl_entrena.fkProfesional == user.id).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> tbl_user:
        db_obj = tbl_user(
            fldBActive=obj_in.fldBActive,
            fldSDireccion=obj_in.fldSDireccion,
            fldSTelefono=obj_in.fldSTelefono,
            fldSImagen=obj_in.fldSImagen,
            fkRol=obj_in.fkRol,
            idPlataforma=obj_in.idPlataforma
        )
        db.add(db_obj)
        db.commit()
        db_obj = self.get_remoto(db=db, id=obj_in.idPlataforma)
        return db_obj

    def update(
            self, db: Session, *, db_obj: tbl_user, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> tbl_user:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def fldBActive(self, user: tbl_user) -> bool:
        return user.fldBActive

    def is_superuser(self, user: tbl_user) -> bool:
        return (user.fkRol == 4)

    def getRol(self, user: tbl_user) -> int:
        return user.fkRol


user = CRUDUser(tbl_user)
