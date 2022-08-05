from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_user
from app.models.tbl_asignado import tbl_asignado
from app.schemas import AsignadoCreate, AsignadoUpdate


class CRUDAsignado(CRUDBase[tbl_asignado, AsignadoCreate, AsignadoUpdate]):

    def count(
            self, db: Session, *, user: int, plan: int
    ) -> int:
        return (
            db.query(self.model)
                .filter(tbl_asignado.fkUsuario == user)
                .filter(tbl_asignado.fkPlan == plan)
                .count()
        )

    def create_with_validation(
            self, db: Session, *, obj_in: AsignadoCreate, user: tbl_user,
    ) -> tbl_asignado:
        obj_in_data = obj_in.dict()
        asignacion = tbl_asignado(**obj_in_data, fkAsignador=user.id)
        db.add(asignacion)
        db.commit()
        db.refresh(asignacion)
        return asignacion


asignado = CRUDAsignado(tbl_asignado)
