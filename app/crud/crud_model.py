from typing import List, Dict, Any, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_model import tbl_model, TrainingStatus, tbl_compra_modelo
from app.schemas.model import ModelCreate, ModelUpdate


class CRUDModel(CRUDBase[tbl_model, ModelCreate, ModelUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: ModelCreate, owner_id: int
    ) -> tbl_model:
        obj_in_data = obj_in.dict()
        devices_in_model = obj_in_data.pop('devices', None)
        movements_in_model = obj_in_data.pop('movements', None)

        db_obj = self.model(**obj_in_data, fkOwner=owner_id)
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
        return db_obj

    def update(
            self, db: Session, *, db_obj: tbl_model, obj_in: Union[ModelUpdate, Dict[str, Any]]
    ) -> tbl_model:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)

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

    def get_multi_by_owner_public(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_model]:
        return (
            db.query(self.model)
            .filter(tbl_model.fkOwner == owner_id).filter(tbl_model.fldBPublico == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_market(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_model]:
        return (
            db.query(self.model)
            .filter(tbl_model.fldBPublico == 1)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_adquiridos(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_model]:
        return (
            db.query(tbl_model)
            .join(tbl_compra_modelo)
            .filter(tbl_model.id == tbl_compra_modelo.fkModelo)
            .filter(tbl_compra_modelo.fkUsuario == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def setPending(
            self, db: Session, *, model: int
    ) -> Any:
        modelo = db.query(tbl_model).get(model)
        if modelo.fldSStatus == TrainingStatus.no_training:
            modelo.fldSStatus = TrainingStatus.no_training_pending
        if modelo.fldSStatus == TrainingStatus.training_succeeded:
            modelo.fldSStatus = TrainingStatus.training_succeeded_pending
        db.commit()
        db.refresh(modelo)
        return modelo


model = CRUDModel(tbl_model)
