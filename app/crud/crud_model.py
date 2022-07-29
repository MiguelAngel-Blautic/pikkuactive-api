from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_model import tbl_model, TrainingStatus
from app.schemas.model import ModelCreate, ModelUpdate


class CRUDModel(CRUDBase[tbl_model, ModelCreate, ModelUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: ModelCreate, owner_id: int
    ) -> tbl_model:
        obj_in_data = obj_in.dict()
        devices_in_model = obj_in_data.pop('devices', None)
        movements_in_model = obj_in_data.pop('movements', None)

        db_obj = self.model(**obj_in_data, fkOwner=owner_id, fkCreador=owner_id)
        db_obj.fldSStatus = TrainingStatus.no_training
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        id_model = db_obj.id
        for device in devices_in_model:
            device = tbl_device(**device, fkOwner=id_model)
            db.add(device)
            db.commit()
            db.refresh(device)

        for movement in movements_in_model:
            movement = tbl_movement(** movement, fkOwner=id_model)
            db.add(movement)
            db.commit()
            db.refresh(movement)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_model]:
        return (
            db.query(self.model)
            .filter(tbl_model.fkOwner == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


model = CRUDModel(tbl_model)
