from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_user
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales
from app.models.tbl_entrena import tbl_entrena
from app.schemas import EntrenaCreate, EntrenaUpdate


class CRUDEntrena(CRUDBase[tbl_entrena, EntrenaCreate, EntrenaUpdate]):

    def create_with_owner(
            self, db: Session, *, obj_in: EntrenaCreate, user: tbl_user,
    ) -> tbl_ejercicio:
        obj_in_data = obj_in.dict()
        if user.fkRol >= 1:
            aceptado = 1
        else:
            aceptado = 0
        entrena = tbl_entrena(**obj_in_data, fldBConfirmed=aceptado)
        db.add(entrena)
        db.commit()
        return entrena


entrena = CRUDEntrena(tbl_entrena)
