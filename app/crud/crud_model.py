from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Device, Movement
from app.models.model import Model, TrainingStatus
from app.schemas.model import ModelCreate, ModelUpdate


class CRUDModel(CRUDBase[Model, ModelCreate, ModelUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: ModelCreate, owner_id: int
    ) -> Model:
        obj_in_data = obj_in.dict()
        devices_in_model = obj_in_data.pop('devices', None)
        movements_in_model = obj_in_data.pop('movements', None)

        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db_obj.status = TrainingStatus.no_training
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        id_model = db_obj.id
        for device in devices_in_model:
            device = Device(**device, owner_id=id_model)
            db.add(device)
            db.commit()
            db.refresh(device)

        for movement in movements_in_model:
            movement = Movement(** movement, owner_id=id_model)
            db.add(movement)
            db.commit()
            db.refresh(movement)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        return (
            db.query(self.model)
            .filter(Model.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


model = CRUDModel(Model)
