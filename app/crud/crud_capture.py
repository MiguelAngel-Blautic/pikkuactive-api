from typing import List

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Mpu, Movement, Device, Model, Ecg
from app.models.capture import Capture
from app.schemas.capture import CaptureCreate, CaptureUpdate


class CRUDCapture(CRUDBase[Capture, CaptureCreate, CaptureUpdate]):
    def create_with_owner(
            self, db: Session, *, obj_in: CaptureCreate, movement: Movement
    ) -> Capture:
        obj_in_data = jsonable_encoder(obj_in)
        mpu_in_capture = obj_in_data.pop('mpu', None)
        ecg_in_capture = obj_in_data.pop('ecg', None)

        db_obj = self.model(**obj_in_data, owner_id=movement.id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        id_capture = db_obj.id
        mpu_list: List[Mpu] = []
        ecg_list: List[Ecg] = []

        for mpu in mpu_in_capture:
            n_device = mpu.pop('n_device', None)
            device = db.query(Device).filter(
                    and_(Device.owner_id == movement.owner_id, Device.number_device == n_device)).first()
            if device is None:
                raise HTTPException(status_code=404, detail="device position {} not found".format(n_device))
            mpu.pop('n_device', None)
            data = Mpu(**mpu, owner_id=id_capture, device_id=device.id)
            mpu_list.append(data)

        for ecg in ecg_in_capture:
            n_device = ecg.get('n_device')
            device = db.query(Device).filter(
                    and_(Device.owner_id == movement.owner_id, Device.number_device == n_device)).first()
            if device is None:
                raise HTTPException(status_code=404, detail="device position {} not found".format(n_device))

            ecg.pop('n_device', None)
            ecg = Ecg(**ecg, owner_id=id_capture, device_id=device.id)
            ecg_list.append(ecg)

        db.add_all(mpu_list)
        db.add_all(ecg_list)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_by_model(
            self, db: Session, model: Model, skip: int = 0, limit: int = 100
    ) -> List[Capture]:
        movements: List[Movement] = db.query(Movement).filter(Movement.owner_id == model.id).all()
        ids_movements = [mov.id for mov in movements]
        return (
            db.query(self.model)
                .filter(Capture.owner_id.in_(ids_movements))
                .offset(skip)
                .limit(limit)
                .all()
        )


capture = CRUDCapture(Capture)
