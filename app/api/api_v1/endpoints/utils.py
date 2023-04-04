import json
from typing import Any, List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic.networks import EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.api.api_v1.endpoints import nn_ecg, nn
from app.api.api_v1.endpoints.models import read_model
from app.models import tbl_model
from app.models.tbl_model import TrainingStatus, tbl_history
from app.utils import send_test_email
import requests
from app.db.session import SessionLocal
import firebase_admin
from firebase_admin import ml
from firebase_admin import credentials
import tensorflow as tf

router = APIRouter()
serverToken = 'AAAAmpw87-E:APA91bGxqsAff2uwrO0uMaaujmiy7nBNCm82HcTFvM0LwsR_7DL-39mNc1JtVj1yEWbjAxepY-ZgdLWkBLo9IoTcUQpuddDoYQJtthQwNriRbJkNDmbfH_v1-UydDVDRinMAW0-9FKF3'
firebase_admin.initialize_app(
    credentials.Certificate('/app/motionia-firebase.json'),
    options={
        'storageBucket': 'motionia-4f3c9.appspot.com',
    })


@router.post("/training/", response_model=schemas.Msg, status_code=201)
def training_model(
        *,
        db: Session = Depends(deps.get_db),
        id_model: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
        background_tasks: BackgroundTasks
) -> Any:
    """
    Get model by ID.
    """
    # Check that the model belongs to the user or if it is superuser
    model: tbl_model = read_model(db=db, id=id_model, current_user=current_user)
    if model.fldSStatus == TrainingStatus.training_started:
        raise HTTPException(status_code=404, detail="Training task already exists")
    background_tasks.add_task(training_task, id_model)
    return {"msg": "ok"}


def training_task(id_model: int):
    print("training_task")
    db: Session = SessionLocal()
    model = db.query(models.tbl_model).filter(models.tbl_model.id == id_model).first()

    # try:
    user = db.query(models.tbl_user).filter(models.tbl_user.id == model.fkOwner).first()
    movements = db.query(models.tbl_movement).filter(models.tbl_movement.fkOwner == model.id).all()
    ids_movements = [mov.id for mov in movements]

    # version_last_mpu = db.query(models.Version).filter(models.Version.owner_id == model.id).order_by(
    #     desc(models.Version.create_time)).first()
    # if version_last_mpu is None:
    #     captures_mpu = db.query(models.Capture).filter(models.Capture.owner_id.in_(ids_movements)).all()
    # else:
    #     captures_mpu = db.query(models.Capture).filter(and_(models.Capture.owner_id.in_(ids_movements),
    #                                                         models.Capture.create_time > version_last_mpu.create_time)).all()



    version_last_mpu = None
    captures_mpu = db.query(models.tbl_capture).filter(or_(models.tbl_capture.fkOwner.in_(ids_movements)), models.tbl_capture.grupo.isnot(None)).all()

    if not captures_mpu or len(captures_mpu) < 2:
        send_notification(fcm_token=user.fldSFcmToken, title='Model: ' + model.fldSName,
                          body='There is not pending captures')
        return False

    model.fldSStatus = TrainingStatus.training_started
    db.commit()
    db.refresh(model)

    # Aqui agregar el la funcion de entrenamiento devolver el link donde se ha guarado el modelo
    # df = nn.data_adapter(model, captures)
    # df_ecg = nn_ecg.data_adapter(model, captures_mpu)
    # version_ecg = nn_ecg.train_model(model, df_ecg, version_last_mpu)
    # version_ecg.fkOwner = model.id

    df_mpu = nn.data_adapter(model, captures_mpu)
    version_mpu = nn.train_model(model, df_mpu, version_last_mpu)
    version_mpu.fkOwner = model.id

    db.add(version_mpu)
    # db.add(version_ecg)

    db.commit()
    db.refresh(version_mpu)
    # db.refresh(version_ecg)

    history = []
    for capture in captures_mpu:
        history.append(tbl_history(fkCapture=capture.id, fkOwner=version_mpu.id))
    version_mpu.history = history
    db.commit()
    db.refresh(version_mpu)

    model.fldSStatus = TrainingStatus.training_succeeded
    db.commit()
    db.refresh(model)
    publish_model_firebase(model, version_mpu.fldSUrl, 'motionia_mpu_')
    # publish_model_firebase(model, version_ecg.fldSUrl, 'ecg_')

    if user.fldSFcmToken:
        send_notification(fcm_token=user.fldSFcmToken, title='Model: ' + model.fldSName, body='finished training')
    db.close()
    return True
    # except BaseException as e:
    #     print('Failed to do something: ' + str(e))
    #     model.status = TrainingStatus.training_failed
    #     db.commit()
    #     db.refresh(model)
    #     db.close()
    #     return False


@router.post("/notification/", response_model=schemas.Msg, status_code=201)
def send_notification(
        fcm_token: str,
        title: str,
        body: str
) -> Any:
    """
    send notification when finishing training.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=' + serverToken,
    }
    body = {
        'notification': {'title': title,
                         'body': body
                         },
        'to': fcm_token,
        'priority': 'high',
        #   'data': dataPayLoad,
    }
    response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))
    print("send_notification: {}".format(response.status_code))

    return {"msg": response.status_code}


def publish_model_firebase(
        model_db: models.tbl_model,
        url: str,
        sub_fij: str
):
    if not model_db.versions:
        return

    model_keras = tf.keras.models.load_model(url)
    exist_model = ml.list_models(list_filter="display_name:" + sub_fij + str(model_db.id)).iterate_all()
    exist_model_id = -1
    for model in exist_model:
        exist_model_id = model.model_id
    if exist_model_id != -1:
        model = ml.get_model(exist_model_id)
        source = ml.TFLiteGCSModelSource.from_keras_model(model_keras)
        model.model_format = ml.TFLiteFormat(model_source=source)
        updated_model = ml.update_model(model)
        ml.publish_model(updated_model.model_id)
    else:
        source = ml.TFLiteGCSModelSource.from_keras_model(model_keras)
        tflite_format = ml.TFLiteFormat(model_source=source)
        model = ml.Model(
            display_name=sub_fij + str(model_db.id),  # This is the name you use from your app to load the model.
            model_format=tflite_format)
        new_model = ml.create_model(model)
        ml.publish_model(new_model.model_id)
