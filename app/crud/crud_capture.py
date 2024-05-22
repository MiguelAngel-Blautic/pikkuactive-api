from typing import List

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_mpu, tbl_movement, tbl_device, tbl_model, tbl_ecg, tbl_dato
from app.models.tbl_capture import tbl_capture
from app.models.tbl_puntos import tbl_puntos
from app.schemas.capture import CaptureCreate, CaptureUpdate


class CRUDCapture(CRUDBase[tbl_capture, CaptureCreate, CaptureUpdate]):
    def create_with_owner(
            self, db: Session, *, obj_in: CaptureCreate, movement: tbl_movement
    ) -> tbl_capture:
        obj_in_data = jsonable_encoder(obj_in)
        data_in_captura = obj_in_data.pop('datos', None)

        db_obj = tbl_capture(fkOwner=movement.id, fldFStart=obj_in.start, fldFMid=obj_in.mid, fldFEnd=obj_in.end, fldFValor=obj_in.valor)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        id_capture = db_obj.id
        datos_list = []

        for dataList in data_in_captura:
            sensor = dataList.pop('sensor', None)
            datos = dataList.pop('data', None)
            for dato in datos:
                datos_list.append(tbl_dato(fldNSample=dato["fldNSample"], fldFValor=dato["fldFValor"], fldFValor2=dato["fldFValor2"], fldFValor3=dato["fldFValor3"],
                             fkCaptura=id_capture, fkDispositivoSensor=sensor))
        db.add_all(datos_list)
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
