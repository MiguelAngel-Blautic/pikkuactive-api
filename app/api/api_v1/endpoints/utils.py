import json
import math
from datetime import datetime
from statistics import mean
from time import strftime
from typing import Any, List

import numpy as np
import pandas as pd
import sa
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.encoders import jsonable_encoder
from fastdtw import fastdtw
from numpy import std
from pydantic.networks import EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count, func

from app import models, schemas
from app.api import deps
from app.api.api_v1.endpoints import nn_ecg, nn, nn_cam, nn2
from app.api.api_v1.endpoints.models import read_model
from app.api.api_v1.endpoints.nn import generar_negativos
from app.api.api_v1.endpoints.nn2 import joinMOV, modelo, remove_outliers
from app.models import tbl_model, tbl_version_estadistica, sensores_estadistica, tbl_movement, tbl_capture, \
    datos_estadistica, tbl_mpu, tbl_dispositivo_sensor, tbl_user, tbl_notificaciones, tbl_registroEstaditica
from app.models.tbl_model import TrainingStatus, tbl_history, tbl_version
from app.schemas import mpu
from app.schemas.capture import CaptureEntrada
from app.schemas.mpu import MpuList
import requests
from app.db.session import SessionLocal
import firebase_admin
from firebase_admin import ml
from firebase_admin import credentials
import tensorflow as tf

router = APIRouter()
serverToken = 'AAAAmpw87-E:APA91bGxqsAff2uwrO0uMaaujmiy7nBNCm82HcTFvM0LwsR_7DL-39mNc1JtVj1yEWbjAxepY-ZgdLWkBLo9IoTcUQpuddDoYQJtthQwNriRbJkNDmbfH_v1-UydDVDRinMAW0-9FKF3'
firebase_admin.initialize_app(
    # credentials.Certificate('/home/diego/PycharmProjects/pikkuactive-api/app/blautic-mm-firebase.json'),
    credentials.Certificate('./app/blautic-mm-firebase.json'),
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
def analizeDatos(*, model: int, datos: List[CaptureEntrada]) -> Any:
    db: Session = SessionLocal()
    modelo = db.query(tbl_model).get(model)
    if not model:
        return ["", "", ""]
    res = nn2.analizeDatos(datos, modelo, db)
    return res


def analize(*, mpus: MpuList) -> Any:
    # print(mpus)
    # print("\n")
    db: Session = SessionLocal()
    res = str(nn2.analize(mpus, db))
    print(res)
    return res


def completar_entrenamiento(db, df, model, version, index):
    inicio = 0
    for i in range(index):
        inicio += (model.dispositivos[i].sensor.fldNFrecuencia * model.fldNDuration)
    sensores = db.query(tbl_dispositivo_sensor).filter(tbl_dispositivo_sensor.fkOwner == model.id).all()
    sensor = sensores[index]
    capturas, l1, l2 = nn2.separarDatos(model.fldSName, df, inicio, inicio + (model.dispositivos[index].sensor.fldNFrecuencia * model.fldNDuration))
    sample = 1
    for i in range(len(l1)):
        media = l1[i]
        desviacion = l2[i]
        dato = datos_estadistica(fkSensor=sensor.id, fkVersion=version.id, fldNSample=sample, fldFStd=desviacion,
                                 fldFMedia=media)
        db.add(dato)
        db.commit()
        db.refresh(dato)
        sample = sample + 1
    return capturas, sensor.id, version.id


@router.get("/entrena_stadistic/")
def entrena_estadistica(id_model: int, db: Session = Depends(deps.get_db)) -> Any:
    model = db.query(models.tbl_model).filter(models.tbl_model.id == id_model).first()
    movements = (db.query(models.tbl_movement).filter(models.tbl_movement.fkOwner == model.id).
                 filter(models.tbl_movement.fldSLabel != "Other").
                 filter(models.tbl_movement.fldSLabel != "other").all())
    ids_movements = [mov.id for mov in movements]
    version = tbl_version_estadistica(fkOwner=model.id, fldSLabel=model.fldSName, accuracy=0)
    db.add(version)
    db.commit()
    db.refresh(version)
    captures_mpu = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).all()
    df_mpu = nn2.data_adapter(model, captures_mpu)
    for i in range(len(model.dispositivos)):
        capturas, sensor, versionId = completar_entrenamiento(db, df_mpu, model, version, i)
        for cap in capturas:
            capturaUsada = tbl_registroEstaditica(fkCaptura=captures_mpu[cap.item()].id, fkSensor=sensor, fkversion=versionId)
            db.add(capturaUsada)
            db.commit()
            db.refresh(capturaUsada)


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
    movements = (db.query(models.tbl_movement).filter(models.tbl_movement.fkOwner == model.id).all())
    ids_movements = [mov.id for mov in movements]
    ids_movementsr = [mov.id for mov in movements if mov.fldSLabel == model.fldSName]

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
    captures_mpur = db.query(models.tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movementsr)).all()

    print(str(len(captures_mpur))+"/"+str(len(captures_mpu)))
    if not captures_mpu or len(captures_mpu) < 2:
        send_notification(fcm_token=user.fldSFcmToken, title='Model: ' + model.fldSName,
                          body='There is not pending captures')
        return False

    model.fldSStatus = TrainingStatus.training_started
    db.commit()
    db.refresh(model)
    try:
        df_mpuR, labelsR, frecuenciasR, cantidadR, nFrecuenciasR = nn.data_adapter3(model, captures_mpur)
        versionRurl = nn.train_model3(model, df_mpuR, labelsR, frecuenciasR, cantidadR, nFrecuenciasR, version_last_mpu)
        df_mpu, labels, frecuencias, cantidad, nFrecuencias = nn.data_adapter2(model, captures_mpu)
        df_mpu, labels = generar_negativos(df_mpu, labels, model.fldSName)
        print("Data Adapter")
        version = nn.train_model2(model, df_mpu, labels, frecuencias, cantidad, nFrecuencias, version_last_mpu)
        version.fkOwner = model.id
        db.add(version)
        db.commit()
        db.refresh(version)
        print("Version save")

        history = []
        for capture in captures_mpu:
            history.append(tbl_history(fkCapture=capture.id, fkOwner=version.id))
        version.history = history
        db.commit()
        db.refresh(version)

        entrena_estadistica(id_model=id_model, db=db)
        model.fldSStatus = TrainingStatus.training_succeeded
        db.commit()
        db.refresh(model)
        publish_model_firebase(model, version.fldSUrl, 'mm_')
        publish_model_firebase(model, versionRurl, 'mmr_')
            # publish_model_firebase(model, version_ecg.fldSUrl, 'ecg_')
    except Exception as Argument:
        print(str(Argument))
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


@router.get("/notificaciones/", response_model=List[str])
def leerNotificaciones(
        *,
        db: Session = Depends(deps.get_db),
        version: str,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    res = []
    mensajes = db.query(tbl_notificaciones).all()
    for m in mensajes:
        add = True
        if m.fldSVersionExclude:
            if version == m.fldSVersionExclude:
                add = False
        if m.fldSVersionInclude:
            if version != m.fldSVersionInclude:
                add = False
        if m.fldNUserExclude:
            if current_user.id == m.fldNUserExclude:
                add = False
        if m.fldNUserInclude:
            if current_user.id != m.fldNUserInclude:
                add = False
        if add:
            res.append(m.fldSTexto)
    return res


@router.get("/getDatasheet/")
def get_datasheet(
        *,
        movement: int,
        db: Session = Depends(deps.get_db)
) -> Any:
    captures = db.query(tbl_capture).filter(tbl_capture.fkOwner == movement).all()
    num = 0
    for cap in captures:
        estado = 1
        s = 0.0
        m = None
        f = 40.0
        datos = [d for d in cap.datos if d.dispositivoSensor.fkSensor == 1]
        i = 0
        while estado == 1:
            if i >= len(datos):
                s = 0
                estado = 2
                pass
            if datos[i].fldFValor < 0.22:
                s = max(0, datos[i].fldNSample - 1)
                estado = 2
            i = i+1
        i = len(datos) - 1
        while estado == 2:
            if i < 0:
                f = 40
                estado = 3
                pass
            if datos[i].fldFValor < -0.3:
                f = min(datos[i].fldNSample + 3, 40)
                estado = 3
            if datos[i].fldFValor > -0.2:
                f = min(datos[i].fldNSample + 3, 40)
                estado = 3
            i = i-1
        if not m:
            m = s + ((f-s)/2)
        cap.fldFStart = (s/40)
        cap.fldFMid = (m/40)
        cap.fldFEnd = (f/40)
        db.commit()
        num = num + 1
        print(str(num) + "/" + str(len(captures)))
    return

@router.get("/datos")
def calcular(
        *,
        db: Session = Depends(deps.get_db)
) -> Any:
    ids_movements = [1723]
    captures = db.query(tbl_capture).filter(models.tbl_capture.fkOwner.in_(ids_movements)).all()
    res = []
    captura = 0
    model = tf.keras.models.load_model("/home/miguelangel/PycharmProjects/pikkuactive-api/static/mulR_b2108b32-0df4-11ef-a7f3-0da8a20e2380.h5")
    for cap in captures:
        captura += 1
        print(captura)
        datos = []
        for i in range(40):
            datos.append([])
        for dato in cap.datos:
            datos[dato.fldNSample].append(dato.fldFValor)
        datas = np.array(datos)
        datas = datas.reshape(1, 40, 6, 1)
        output = model.predict(datas)
        res.append([output[0][0], output[0][1], output[0][2], cap.id])
    print(res)




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


@router.get("/dashboard/")
def dashboard(inicio: datetime, fin: datetime, db: Session = Depends(deps.get_db)) -> Any:
    usuarios = len(db.query(tbl_user).filter(tbl_user.fldFCreacion >= inicio).filter(
        tbl_user.fldFCreacion <= fin).all())
    modelos = db.query(tbl_model).filter(tbl_model.fldDTimeCreateTime >= inicio).filter(
        tbl_model.fldDTimeCreateTime <= fin).all()
    creacion_modelos = db.query(func.count(tbl_model.id), func.date(tbl_model.fldDTimeCreateTime)).filter(tbl_model.fldDTimeCreateTime >= inicio).filter(
        tbl_model.fldDTimeCreateTime <= fin).group_by(func.date(tbl_model.fldDTimeCreateTime)).all()
    Lcreacion_modelos = []
    for num in creacion_modelos:
        Lcreacion_modelos.append({"valor": num[0], "fecha": num[1]})
    creacion_usuarios = db.query(func.count(tbl_user.id), func.date(tbl_user.fldFCreacion)).filter(tbl_user.fldFCreacion >= inicio).filter(
        tbl_user.fldFCreacion <= fin).group_by(func.date(tbl_user.fldFCreacion)).all()
    Lcreacion_usuarios = []
    for num in creacion_usuarios:
        Lcreacion_usuarios.append({"valor": num[0], "fecha": num[1]})
    versiones = db.query(tbl_version).filter(tbl_version.fldDTimeCreateTime >= inicio).filter(
        tbl_version.fldDTimeCreateTime <= fin).all()
    modelos_tipo1 = len([model for model in modelos if model.fkTipo == 1])
    modelos_tipo2 = len([model for model in modelos if model.fkTipo == 2])
    sensores = len([model.dispositivos for model in modelos])
    return {"creacion_modelos": Lcreacion_modelos,
            "creacion_usuarios": Lcreacion_usuarios,
            "usuarios": usuarios,
            "modelos_tipo": [{"tipo": "Movimiento", "valor": modelos_tipo1}, {"tipo": "Puntos", "valor": modelos_tipo2}],
            "dispositivos": (sensores/len(modelos)),
            "entrenamientos": len(versiones),
            "sensores_tipo": [{"tipo": "PIKKU/Ziven", "valor": modelos_tipo1}, {"tipo": "Cámara", "valor": modelos_tipo2}],
            "modelos": len(modelos)}
