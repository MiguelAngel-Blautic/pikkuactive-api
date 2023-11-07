import json
from statistics import mean
from typing import Any, List

import pandas as pd
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from numpy import std
from pydantic.networks import EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.api.api_v1.endpoints import nn_ecg, nn, nn_cam, nn2
from app.api.api_v1.endpoints.models import read_model
from app.api.api_v1.endpoints.nn2 import joinMOV, modelo
from app.models import tbl_model, tbl_version_estadistica, sensores_estadistica, tbl_movement, tbl_capture, datos_estadistica, tbl_mpu
from app.models.tbl_model import TrainingStatus, tbl_history
from app.schemas import mpu
from app.schemas.mpu import MpuList
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
    credentials.Certificate('/home/diego/PycharmProjects/pikkuactive-api/app/blautic-mm-firebase.json'),
    # credentials.Certificate('./app/blautic-mm-firebase.json'),
    options={
        'storageBucket': 'blautic-mm.appspot.com',
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


@router.post("/analize/")
def analize(*, mpus: MpuList) -> Any:
    # print(mpus)
    # print("\n")
    db: Session = SessionLocal()
    res = str(nn2.analize(mpus, db))
    print(res)
    return res


def completar_entrenamiento(db, df, columns, orden, nombre, model, version):
    max = df.max().max()
    min = df.min().min()
    # df = (df - min) / (max - min)
    sensor = db.query(sensores_estadistica).filter(sensores_estadistica.fkModelo == model.id).filter(sensores_estadistica.fldNOrden == orden).first()
    if not sensor:
        sensor = sensores_estadistica(fkModelo=model.id, fldNOrden=orden, fldSNombre=nombre, fldFMax=max, fldFMin=min)
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
    sample = 1
    for column in columns:
        media = mean(df[column])
        desviacion = std(df[column])
        dato = datos_estadistica(fkSensor=sensor.id, fkVersion=version.id, fldNSample=sample, fldFStd=desviacion, fldFMedia=media)
        db.add(dato)
        db.commit()
        db.refresh(dato)
        sample = sample + 1
    pass


@router.get("/entrena_stadistic/")
def entrena_estadistica(id_model: int, db: Session = Depends(deps.get_db)) -> Any:
    model = db.query(models.tbl_model).filter(models.tbl_model.id == id_model).first()
    if not model:
        raise HTTPException(status_code=404, detail="Unknow ID")
    movements = db.query(tbl_movement).filter(tbl_movement.fkOwner == model.id).all()
    for movement in movements:
        if movement.fldSLabel == 'Other' or movement.fldSLabel == 'other':
            continue
        version = tbl_version_estadistica(fkOwner=model.id, fldSLabel=movement.fldSLabel, accuracy=0)
        db.add(version)
        db.commit()
        db.refresh(version)
        captures = db.query(tbl_capture).filter(tbl_capture.fkOwner == movement.id).all()
        for device in model.devices:
            if device.fldNSensores == 1:  # MPU
                columns = []
                FREQ = 20
                for i in range(model.fldNDuration * FREQ):
                    columns.append("Sample-" + str(i + 1))
                loc = 0
                dfAccX = pd.DataFrame(columns=columns)
                dfAccY = pd.DataFrame(columns=columns)
                dfAccZ = pd.DataFrame(columns=columns)
                dfGyrX = pd.DataFrame(columns=columns)
                dfGyrY = pd.DataFrame(columns=columns)
                dfGyrZ = pd.DataFrame(columns=columns)
                for capture in captures:
                    # mpus = db.query(tbl_mpu).filter(tbl_mpu.fkOwner == capture.id).all()
                    accX = [mpu.fldFAccX for mpu in capture.mpu]
                    accY = [mpu.fldFAccY for mpu in capture.mpu]
                    accZ = [mpu.fldFAccZ for mpu in capture.mpu]
                    gyrX = [mpu.fldFGyrX for mpu in capture.mpu]
                    gyrY = [mpu.fldFGyrY for mpu in capture.mpu]
                    gyrZ = [mpu.fldFGyrZ for mpu in capture.mpu]
                    dfAccX.loc[loc] = accX
                    dfAccY.loc[loc] = accY
                    dfAccZ.loc[loc] = accZ
                    dfGyrX.loc[loc] = gyrX
                    dfGyrY.loc[loc] = gyrY
                    dfGyrZ.loc[loc] = gyrZ
                    loc = loc + 1
                completar_entrenamiento(db, dfAccX, columns, 1, 'AccX', model, version)
                completar_entrenamiento(db, dfAccY, columns, 2, 'AccY', model, version)
                completar_entrenamiento(db, dfAccZ, columns, 3, 'AccZ', model, version)
                completar_entrenamiento(db, dfGyrX, columns, 4, 'GyrX', model, version)
                completar_entrenamiento(db, dfGyrY, columns, 5, 'GyrY', model, version)
                completar_entrenamiento(db, dfGyrZ, columns, 6, 'GyrZ', model, version)
    return 1


@router.post("/analize_stadistic/")
def analize_estadistica(mpus: MpuList, model: int, db: Session = Depends(deps.get_db)) -> Any:
    model = db.query(tbl_model).get(model)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return 1


@router.post("/entrena/")
def entrena(id_model: int) -> Any:
    db: Session = SessionLocal()
    model = db.query(models.tbl_model).filter(models.tbl_model.id == id_model).first()
    user = db.query(models.tbl_user).filter(models.tbl_user.id == model.fkOwner).first()
    movements = db.query(models.tbl_movement).filter(models.tbl_movement.fkOwner == model.id).all()
    ids_movements = [mov.id for mov in movements]
    # captures_mpu = db.query(models.tbl_capture).filter(or_(models.tbl_capture.fkOwner.in_(ids_movements)), models.tbl_capture.grupo.isnot(None)).all()
    captures_mpu = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).all()
    if not captures_mpu or len(captures_mpu) < 2:
        send_notification(fcm_token=user.fldSFcmToken, title='Model: ' + model.fldSName,
                          body='There is not pending captures')
        return False
    df_mpu, accX, accY, accZ, gyrX, gyrY, gyrZ = nn2.data_adapter(model, captures_mpu)
    print(modelo(df_mpu, model.fldSName, accX, accY, accZ, gyrX, gyrY, gyrZ))


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
    # captures_mpu = db.query(models.tbl_capture).filter(or_(models.tbl_capture.fkOwner.in_(ids_movements)), models.tbl_capture.grupo.isnot(None)).all()
    captures_mpu = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).all()

    if not captures_mpu or len(captures_mpu) < 2:
        send_notification(fcm_token=user.fldSFcmToken, title='Model: ' + model.fldSName,
                          body='There is not pending captures')
        return False

    model.fldSStatus = TrainingStatus.training_started
    db.commit()
    db.refresh(model)
    try:
        # Aqui agregar el la funcion de entrenamiento devolver el link donde se ha guarado el modelo
        # df = nn.data_adapter(model, captures)
        # df_ecg = nn_ecg.data_adapter(model, captures_mpu)
        # version_ecg = nn_ecg.train_model(model, df_ecg, version_last_mpu)
        # version_ecg.fkOwner = model.id
        # db.add(version_ecg)

        if model.fkTipo == 1:
            df_mpu = nn.data_adapter(model, captures_mpu)
            version_mpu = nn.train_model(model, df_mpu, version_last_mpu)
            version_mpu.fkOwner = model.id

            db.add(version_mpu)

            db.commit()
            db.refresh(version_mpu)
        if model.fkTipo == 2:
            df_cam = nn_cam.data_adapter(model, captures_mpu)
            version_cam = nn_cam.train_model(model, df_cam, version_last_mpu)
            version_cam.fkOwner = model.id
            db.add(version_cam)
            db.commit()
            db.refresh(version_cam)
        # db.refresh(version_ecg)

        history = []
        for capture in captures_mpu:
            if model.fkTipo == 1:
                history.append(tbl_history(fkCapture=capture.id, fkOwner=version_mpu.id))
            if model.fkTipo == 2:
                history.append(tbl_history(fkCapture=capture.id, fkOwner=version_cam.id))

        if model.fkTipo == 1:
            version_mpu.history = history
            db.commit()
            db.refresh(version_mpu)
        if model.fkTipo == 2:
            version_cam.history = history
            db.commit()
            db.refresh(version_cam)

        model.fldSStatus = TrainingStatus.training_succeeded
        db.commit()
        db.refresh(model)
        if model.fkTipo == 1:
            publish_model_firebase(model, version_mpu.fldSUrl, 'mm_mpu_')
        if model.fkTipo == 2:
            publish_model_firebase(model, version_cam.fldSUrl, 'mm_cam_')
        # publish_model_firebase(model, version_ecg.fldSUrl, 'ecg_')
    except:
        model.fldSStatus = TrainingStatus.training_failed
        db.commit()
        db.refresh(model)
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
