from typing import List

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_mpu, tbl_movement, tbl_device, tbl_model, tbl_ecg
from app.models.tbl_capture import tbl_capture
from app.models.tbl_puntos import tbl_puntos
from app.schemas.capture import CaptureCreate, CaptureUpdate


class CRUDCapture(CRUDBase[tbl_capture, CaptureCreate, CaptureUpdate]):
    def create_with_owner(
            self, db: Session, *, obj_in: CaptureCreate, movement: tbl_movement
    ) -> tbl_capture:
        obj_in_data = jsonable_encoder(obj_in)
        mpu_in_capture = obj_in_data.pop('mpu', None)
        ecg_in_capture = obj_in_data.pop('ecg', None)
        cam_in_capture = obj_in_data.pop('cam', None)

        db_obj = self.model(**obj_in_data, fkOwner=movement.id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        id_capture = db_obj.id
        mpu_list: List[tbl_mpu] = []
        ecg_list: List[tbl_ecg] = []
        cam_list: List[tbl_puntos] = []

        for mpu in mpu_in_capture:
            n_device = mpu.pop('fkDevice', None)
            print(n_device)
            print(movement.fkOwner)
            device = db.query(tbl_device).filter(
                    and_(tbl_device.fkOwner == movement.fkOwner, tbl_device.fldNNumberDevice == n_device)).first()
            if device is None:
                raise HTTPException(status_code=404, detail="device position {} not found".format(n_device))
            mpu.pop('fkDevice', None)
            data = tbl_mpu(**mpu, fkOwner=id_capture, fkDevice=device.id)
            mpu_list.append(data)

        for ecg in ecg_in_capture:
            n_device = ecg.get('fkDevice')
            device = db.query(tbl_device).filter(
                    and_(tbl_device.fkOwner == movement.fkOwner, tbl_device.fldNNumberDevice == n_device)).first()
            if device is None:
                raise HTTPException(status_code=404, detail="device position {} not found".format(n_device))

            ecg.pop('fkDevice', None)
            ecg = tbl_ecg(**ecg, fkOwner=id_capture, fkDevice=device.id)
            ecg_list.append(ecg)

        for cam in cam_in_capture:
            n_device = cam.get('fkDevice')
            device = db.query(tbl_device).filter(
                and_(tbl_device.fkOwner == movement.fkOwner, tbl_device.fldNNumberDevice == n_device)).first()
            if device is None:
                raise HTTPException(status_code=404, detail="device position {} not found".format(n_device))

            cam.pop('fkDevice', None)
            cam = tbl_puntos(**cam, fkOwner=id_capture, fkDevice=device.id)
            cam_list.append(cam)
        db.add_all(mpu_list)
        db.add_all(ecg_list)
        db.add_all(cam_list)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_by_model(
            self, db: Session, model: tbl_model, skip: int = 0, limit: int = 100
    ) -> List[tbl_capture]:
        movements: List[tbl_movement] = db.query(tbl_movement).filter(tbl_movement.fkOwner == model.id).all()
        ids_movements = [mov.id for mov in movements]
        return (
            db.query(self.model)
                .filter(tbl_capture.fkOwner.in_(ids_movements))
                .offset(skip)
                .limit(limit)
                .all()
        )


capture = CRUDCapture(tbl_capture)
