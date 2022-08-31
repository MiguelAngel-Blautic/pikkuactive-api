from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.tbl_entrena import tbl_entrena
from app.models.tbl_user import tbl_user
from app.schemas.user import UserCreate, UserUpdate, User


class CRUDUser(CRUDBase[tbl_user, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[tbl_user]:
        return db.query(tbl_user).filter(tbl_user.fldSEmail == email).first()

    def get_centros(self, db: Session, *, user: int, skip: int = 0, limit: int = 100) -> Optional[List[User]]:
        centros = db.query(tbl_user).filter(tbl_user.fkRol == 3).offset(skip).limit(limit).all()
        res = []
        for centro in centros:
            obj = User()
            obj.id = centro.id
            obj.fldSFullName = centro.fldSFullName
            obj.fldSEmail = centro.fldSEmail
            obj.fldBActive = centro.fldBActive
            obj.fldSDireccion = centro.fldSDireccion
            obj.fldSTelefono = centro.fldSTelefono
            obj.fldSImagen = centro.fldSImagen
            obj.fkRol = centro.fkRol
            obj.progreso = 50
            aux = db.query(tbl_entrena).filter(tbl_entrena.fkUsuario == user).filter(tbl_entrena.fkProfesional == centro.id).first()
            if aux:
                obj.idRelacion = aux.id
                if aux.fldBConfirmed:
                    obj.estado = 2
                else:
                    obj.estado = 1
            else:
                obj.estado = 0
            res.append(obj)
        return res

    def get_clientes(self, db: Session, *, user: int, rol: int) -> Optional[List[User]]:
        global clientes
        res = []
        if rol == 2:
            aux = db.query(tbl_entrena.fkProfesional).filter(tbl_entrena.fkUsuario == user).first()
            print(aux)
            if aux:
                id = aux[0]
                clientes = db.query(tbl_user).outerjoin(tbl_entrena, tbl_user.id == tbl_entrena.fkUsuario).filter(tbl_entrena.fkProfesional == id). \
                    filter(tbl_user.fkRol == 1).filter(tbl_entrena.fldBConfirmed).all()
        else:
            id = user
            clientes = db.query(tbl_user).outerjoin(tbl_entrena, tbl_user.id == tbl_entrena.fkUsuario).filter(tbl_entrena.fkProfesional == id).all()

        for cliente in clientes:
            obj = User()
            obj.id = cliente.id
            obj.fldSFullName = cliente.fldSFullName
            obj.fldSEmail = cliente.fldSEmail
            obj.fldBActive = cliente.fldBActive
            obj.fldSDireccion = cliente.fldSDireccion
            obj.fldSTelefono = cliente.fldSTelefono
            obj.fldSImagen = cliente.fldSImagen
            obj.fkRol = cliente.fkRol
            obj.progreso = 50
            aux = db.query(tbl_entrena).filter(tbl_entrena.fkUsuario == obj.id).filter(tbl_entrena.fkProfesional == id).first()
            if aux:
                obj.idRelacion = aux.id
                if aux.fldBConfirmed:
                    obj.estado = 2
                else:
                    obj.estado = 1
            else:
                obj.estado = 0
            res.append(obj)
        return res

    def get_profesionales(self, db: Session, *, skip: int = 0, limit: int = 100, user: tbl_user) -> Optional[List[tbl_user]]:
        if user.fkRol == 3:
            return db.query(tbl_user).outerjoin(tbl_entrena, tbl_entrena.fkUsuario == tbl_user.id).filter(tbl_user.fkRol == 2). \
                filter(tbl_entrena.fkProfesional == user.id).offset(skip).limit(limit).all()
        if user.fkRol == 4:
            return db.query(tbl_user).filter(tbl_user.fkRol == 2).offset(skip).limit(limit).all()

    def get_pacientes(self, db: Session, *, skip: int = 0, limit: int = 100, user: tbl_user) -> Optional[List[tbl_user]]:
        if user.fkRol == 2:
            centro = db.query(tbl_user).outerjoin(tbl_entrena, tbl_entrena.fkProfesional == tbl_user.id). \
                filter(tbl_entrena.fkUsuario == user.id).offset(skip).limit(limit).first()
            return db.query(tbl_user).outerjoin(tbl_entrena, tbl_entrena.fkUsuario == tbl_user.id).filter(tbl_user.fkRol == 1). \
                filter(tbl_entrena.fkProfesional == centro.id).offset(skip).limit(limit).all()
        if user.fkRol == 3:
            return db.query(tbl_user).outerjoin(tbl_entrena, tbl_entrena.fkUsuario == tbl_user.id).filter(tbl_user.fkRol == 1). \
                filter(tbl_entrena.fkProfesional == user.id).offset(skip).limit(limit).all()
        if user.fkRol == 4:
            return db.query(tbl_user).filter(tbl_user.fkRol == 1).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> tbl_user:
        db_obj = tbl_user(
            fldSFullName=obj_in.fldSFullName,
            fldSEmail=obj_in.fldSEmail,
            fldSHashedPassword=get_password_hash(obj_in.fldSHashedPassword),
            fldBActive=obj_in.fldBActive,
            fkRol=obj_in.fkRol,
        )
        db.add(db_obj)
        db.commit()
        db_obj = self.get_by_email(db=db, email=obj_in.fldSEmail)
        return db_obj

    def update(
            self, db: Session, *, db_obj: tbl_user, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> tbl_user:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[tbl_user]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.fldSHashedPassword):
            return None
        return user

    def fldBActive(self, user: tbl_user) -> bool:
        return user.fldBActive

    def is_superuser(self, user: tbl_user) -> bool:
        return (user.fkRol == 4)

    def getRol(self, user: tbl_user) -> int:
        return user.fkRol


user = CRUDUser(tbl_user)
