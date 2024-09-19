from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_model, tbl_capture, tbl_movement, sensores_estadistica, tbl_version_estadistica, \
    datos_estadistica, tbl_user, tbl_dispositivo_sensor, tbl_tipo_sensor, tbl_position, tbl_image_device
from app.models.tbl_model import tbl_categorias, tbl_compra_modelo, tbl_history, tbl_imagenes
from app.schemas import MovementCreate, Version, Position, ImageDevice
from app.schemas.capture import CaptureResumen
from app.schemas.device import DeviceSensor, Device, DeviceCreate, DeviceSensorCreate
from app.schemas.model import ModelStadistics, ModelStadisticsSensor, Model, ModelCreate
from app.schemas.movement import MovementCaptures, Movement

router = APIRouter()


@router.get("/user/", response_model=List[schemas.Model])
def read_models(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        isDevices: int = 1,
        complete: int = 1,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    if crud.user.is_superuser(current_user):
        model: List[tbl_model] = crud.model.get_multi(db, skip=skip, limit=limit)
    else:
        model = crud.model.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    res = []
    for m in model:
        res.append(read_model_datas(m=m, user=current_user.id, db=db, complete=complete))
    db.close()
    return res[::-1]


@router.get("/{id}", response_model=schemas.Model)
def read_model_server(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        complete: int = 1,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    res = read_model(db=db, id=id, complete=complete, current_user=current_user)
    db.close()
    return res


def read_model(
        *,
        db: Session,
        id: int,
        complete: int,
        current_user: models.tbl_user,
) -> Any:
    """
    Get model by ID.
    """
    m = crud.model.get(db=db, id=id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (m.fkOwner == current_user.id) or (m.fldBPublico == 1)):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return read_model_datas(m=m, db=db, user=current_user.id, complete=complete)


@router.get("/open/{id}", response_model=schemas.Model)
def read_model_open(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        complete: int = 1,
        token: str
) -> Any:
    """
    Get model by ID.
    """
    m = crud.model.get(db=db, id=id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (m.fldSToken == token):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    res = read_model_datas(m=m, db=db, user=0, complete=complete)
    db.close()
    return res


@router.get("/clone/{id}")
def clonar_model(
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    devices = []
    for device in model.devices:
        devices.append(DeviceCreate(fldNNumberDevice=device.fldNNumberDevice,
                                    fldNSensores=device.fldNSensores,
                                    fkPosition=device.fkPosition))
    dispositivos = []
    for dispositivo in model.dispositivos:
        dispositivos.append(DeviceSensorCreate(fkPosicion=dispositivo.fkPosicion,
                                               fkSensor=dispositivo.fkSensor))
    model_in = ModelCreate(fldSName=model.fldSName + "_copia",
                           fldNDuration=model.fldNDuration,
                           devices=devices,
                           dispositivos=dispositivos)
    modelo = crud.model.create_with_owner(db=db, obj_in=model_in, owner_id=current_user.id)
    movement_correct = MovementCreate(fldSLabel=modelo.fldSName, fldSDescription=modelo.fldSName)
    crud.movement.create_with_owner(db=db, obj_in=movement_correct, fkOwner=modelo.id)
    movement_incorrect = MovementCreate(fldSLabel="Other", fldSDescription="Other")
    crud.movement.create_with_owner(db=db, obj_in=movement_incorrect, fkOwner=modelo.id)
    db.close()
    return model


@router.get("/user/{id}", response_model=List[schemas.Model])
def read_models(
        id: int,
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    user = db.query(tbl_user).filter(tbl_user.idPlataforma == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    model = crud.model.get_multi_by_owner_public(
        db=db, owner_id=user.id, skip=skip, limit=limit
    )
    res = []
    for m in model:
        versions = []
        cant = 0
        for v in m.versions:
            capturas = db.query(tbl_history).filter(tbl_history.fkOwner == v.id).all()

            versions.append(Version(id=v.id,
                                    fkOwner=v.fkOwner,
                                    fldDTimeCreateTime=v.fldDTimeCreateTime,
                                    fldFAccuracy=v.fldFAccuracy,
                                    fldNEpoch=v.fldNEpoch,
                                    fldFLoss=v.fldFLoss,
                                    fldSOptimizer=v.fldSOptimizer,
                                    fldFLearningRate=v.fldFLearningRate,
                                    capturesCount=len(capturas) - cant))
            cant = len(capturas)
        dispositivos = []
        devices = m.devices
        crearDevices = len(devices) < 1
        posicion = -1
        nDevices = 0
        if crearDevices:
            devices = []
        for d in m.dispositivos:
            dispositivos.append(DeviceSensor(
                id=d.id,
                fkPosicion=d.fkPosicion,
                fkSensor=d.fkSensor,
                fkOwner=d.fkOwner))
            if crearDevices and d.fkPosicion != posicion:
                posicion = d.fkPosicion
                nDevices += 1
                if d.fkSensor <= 6:
                    nsensores = 6
                else:
                    nsensores = 17
                pos = db.query(tbl_position).get(d.fkPosicion)
                devices.append(Device(id=d.id,
                                      fldNNumberDevice=nDevices,
                                      fkPosition=posicion,
                                      fkOwner=d.fkOwner,
                                      position=Position(fldSName=pos.fldSName, fldSDescription=pos.fldSDescription,
                                                        id=pos.id),
                                      fldNSensores=nsensores
                                      ))

        res.append(Model(id=m.id,
                         fldSName=m.fldSName,
                         fldSDescription=m.fldSDescription,
                         fldNDuration=m.fldNDuration,
                         fldBPublico=m.fldBPublico,
                         fkCategoria=m.fkCategoria,
                         fldFPrecio=m.fldFPrecio,
                         fkTipo=m.fkTipo,
                         fkOwner=m.fkOwner,
                         fldDTimeCreateTime=m.fldDTimeCreateTime,
                         fldSStatus=m.fldSStatus,
                         fldNProgress=m.fldNProgress,
                         movements=m.movements,
                         devices=devices,
                         versions=versions[::-1],
                         dispositivos=dispositivos,
                         tuyo=(m.fkOwner == current_user.id),
                         fldBRegresivo=m.fldBRegresivo,
                         fldFMinValor=m.fldFMinValor,
                         fldFMaxValor=m.fldFMaxValor,
                         fldSNomValor=m.fldSNomValor,
                         fldSToken=m.fldSToken))
    db.close()
    return res[::-1]


@router.get("/marketplace/", response_model=List[schemas.Model])
def read_models_marketplace(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    models = crud.model.get_multi_market(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    res = []
    for m in models:
        versions = []
        cant = 0
        for v in m.versions:
            capturas = db.query(tbl_history).filter(tbl_history.fkOwner == v.id).all()

            versions.append(Version(id=v.id,
                                    fkOwner=v.fkOwner,
                                    fldDTimeCreateTime=v.fldDTimeCreateTime,
                                    fldFAccuracy=v.fldFAccuracy,
                                    fldNEpoch=v.fldNEpoch,
                                    fldFLoss=v.fldFLoss,
                                    fldSOptimizer=v.fldSOptimizer,
                                    fldFLearningRate=v.fldFLearningRate,
                                    capturesCount=len(capturas) - cant))
            cant = len(capturas)
        dispositivos = []
        devices = m.devices
        crearDevices = len(devices) < 1
        posicion = -1
        nDevices = 0
        if crearDevices:
            devices = []
        for d in m.dispositivos:
            dispositivos.append(DeviceSensor(
                id=d.id,
                fkPosicion=d.fkPosicion,
                fkSensor=d.fkSensor,
                fkOwner=d.fkOwner))
            if crearDevices and d.fkPosicion != posicion:
                posicion = d.fkPosicion
                nDevices += 1
                if d.fkSensor <= 6:
                    nsensores = 6
                else:
                    nsensores = 17
                pos = db.query(tbl_position).get(d.fkPosicion)
                devices.append(Device(id=d.id,
                                      fldNNumberDevice=nDevices,
                                      fkPosition=posicion,
                                      fkOwner=d.fkOwner,
                                      position=Position(fldSName=pos.fldSName, fldSDescription=pos.fldSDescription,
                                                        id=pos.id),
                                      fldNSensores=nsensores
                                      ))

        res.append(Model(id=m.id,
                         fldSName=m.fldSName,
                         fldSDescription=m.fldSDescription,
                         fldNDuration=m.fldNDuration,
                         fldBPublico=m.fldBPublico,
                         fkCategoria=m.fkCategoria,
                         fldFPrecio=m.fldFPrecio,
                         fkTipo=m.fkTipo,
                         fkOwner=m.fkOwner,
                         fldDTimeCreateTime=m.fldDTimeCreateTime,
                         fldSStatus=m.fldSStatus,
                         fldNProgress=m.fldNProgress,
                         movements=m.movements,
                         devices=devices,
                         versions=versions[::-1],
                         dispositivos=dispositivos,
                         tuyo=(m.fkOwner == current_user.id),
                         fldBRegresivo=m.fldBRegresivo,
                         fldFMinValor=m.fldFMinValor,
                         fldFMaxValor=m.fldFMaxValor,
                         fldSNomValor=m.fldSNomValor,
                         fldSToken=m.fldSToken))
    db.close()
    return res[::-1]


@router.get("/adquiridos/", response_model=List[schemas.Model])
def read_models_adquiridos(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    res = crud.model.get_multi_adquiridos(db=db, owner_id=current_user.id, skip=skip, limit=limit)[::-1]
    db.close()
    return res


@router.post("/", response_model=schemas.Model)
def create_model(
        *,
        db: Session = Depends(deps.get_db),
        model_in: schemas.ModelCreate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new model.
    """
    model_in.fldBPublico = 0  # De momento para forzarlos a ser privados por ahora
    model = crud.model.create_with_owner(db=db, obj_in=model_in, owner_id=current_user.id)
    movement_correct = MovementCreate(fldSLabel=model.fldSName, fldSDescription=model.fldSName)
    crud.movement.create_with_owner(db=db, obj_in=movement_correct, fkOwner=model.id)
    movement_incorrect = MovementCreate(fldSLabel="Other", fldSDescription="Other")
    crud.movement.create_with_owner(db=db, obj_in=movement_incorrect, fkOwner=model.id)
    db.close()
    return model


@router.put("/comprar/")
def comprar_model(
        *,
        db: Session = Depends(deps.get_db),
        model: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    modelo = crud.model.get(db=db, id=model)
    if not modelo:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (modelo.fldBPublico == 1 or modelo.fkOwner == current_user.id):
        raise HTTPException(status_code=502, detail="Not available for purchase")
    obj = tbl_compra_modelo()
    obj.fkModelo = model
    obj.fkUsuario = current_user.id
    obj.fldDFecha = datetime.now()
    db.add(obj)
    db.commit()
    db.close()
    return "ok"


@router.delete("/comprar/")
def deshacer_compra(
        *,
        db: Session = Depends(deps.get_db),
        model: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    registro = db.query(tbl_compra_modelo).filter(tbl_compra_modelo.fkUsuario == current_user.id).filter(
        tbl_compra_modelo.fkModelo == model).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(registro)
    db.commit()
    db.close()
    return "ok"


@router.delete("/")
def delete_model(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete existing model
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (
            crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id))):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    db.delete(model)
    db.commit()
    db.close()
    return 1




@router.put("/sensorimage/")
def addImageModel(
        *,
        imageDevice: ImageDevice,
        db: Session = Depends(deps.get_db),
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    imagenes = db.query(tbl_image_device).filter(tbl_image_device.fkModel == imageDevice.fkModel).filter(
        tbl_image_device.fkPosition == imageDevice.fkPosition).all()
    for i in imagenes:
        db.delete(i)
        db.commit()
    image = tbl_image_device(fkModel=imageDevice.fkModel, fkPosition=imageDevice.fkPosition, fldSImage=imageDevice.fldSImage)
    db.add(image)
    db.commit()
    return 1


@router.get("/imagen/")
def readVideoImagen(
        *,
        model: int,
        video: int = 1,
        imagen: int = 1,
        db: Session = Depends(deps.get_db)
) -> Any:
    modelo = db.query(tbl_model).get(model)
    if not modelo:
        raise HTTPException(status_code=404, detail="Model not found")
    vid = ""
    img = ""
    if imagen == 1:
        img = modelo.fldSImage
    if video == 1:
        vid = modelo.fldSVideo
    return {"imagen": img, "video": vid}


def read_model_datas(
        *,
        m: tbl_model,
        user: int,
        db: Session,
        complete: int
) -> Any:
    versions = []
    if complete == 1:
        cant = 0
        for v in m.versions:
            capturas = db.query(tbl_history).filter(tbl_history.fkOwner == v.id).all()

            versions.append(Version(id=v.id,
                                    fkOwner=v.fkOwner,
                                    fldDTimeCreateTime=v.fldDTimeCreateTime,
                                    fldFAccuracy=v.fldFAccuracy,
                                    fldNEpoch=v.fldNEpoch,
                                    fldFLoss=v.fldFLoss,
                                    fldSOptimizer=v.fldSOptimizer,
                                    fldFLearningRate=v.fldFLearningRate,
                                    capturesCount=len(capturas) - cant))
            cant = len(capturas)
    dispositivos = []
    devices = m.devices
    crearDevices = True  # len(devices) < 1
    posicion = -1
    nDevices = 0
    if crearDevices:
        devices = []
    for d in m.dispositivos:
        dispositivos.append(DeviceSensor(
            id=d.id,
            fkPosicion=d.fkPosicion,
            fkSensor=d.fkSensor,
            fkOwner=d.fkOwner))
        if crearDevices and d.fkPosicion != posicion:
            posicion = d.fkPosicion
            nDevices += 1
            if d.fkSensor <= 6:
                nsensores = 6
            else:
                nsensores = 17
            pos = db.query(tbl_position).get(d.fkPosicion)
            img = db.query(tbl_image_device).filter(tbl_image_device.fkModel == m.id).filter(
                tbl_image_device.fkPosition == pos.id).first()
            imagen = None
            if img:
                imagen = img.fldSImage
            devices.append(Device(id=d.id,
                                  fldNNumberDevice=nDevices,
                                  fkPosition=posicion,
                                  fkOwner=d.fkOwner,
                                  position=Position(fldSName=pos.fldSName, fldSDescription=pos.fldSDescription,
                                                    id=pos.id),
                                  fldNSensores=nsensores,
                                  imagen=imagen
                                  ))
    if complete == 1:
        mod = Model(id=m.id,
                    fldSName=m.fldSName,
                    fldSDescription=m.fldSDescription,
                    fldNDuration=m.fldNDuration,
                    fldBPublico=m.fldBPublico,
                    fkCategoria=m.fkCategoria,
                    fldFPrecio=m.fldFPrecio,
                    fkTipo=m.fkTipo,
                    fkOwner=m.fkOwner,
                    fldDTimeCreateTime=m.fldDTimeCreateTime,
                    fldSStatus=m.fldSStatus,
                    fldNProgress=m.fldNProgress,
                    movements=m.movements,
                    devices=devices,
                    versions=versions[::-1],
                    dispositivos=dispositivos,
                    imagen=m.fldSImage,
                    video=m.fldSVideo,
                    tuyo=(m.fkOwner == user),
                    fldBRegresivo=m.fldBRegresivo,
                    fldFMinValor=m.fldFMinValor,
                    fldFMaxValor=m.fldFMaxValor,
                    fldSNomValor=m.fldSNomValor,
                    fldSToken=m.fldSToken)
    else:
        mod = Model(id=m.id,
                    fldSName=m.fldSName,
                    fldSDescription=m.fldSDescription,
                    fldNDuration=m.fldNDuration,
                    fldBPublico=m.fldBPublico,
                    fkCategoria=m.fkCategoria,
                    fldFPrecio=m.fldFPrecio,
                    fkTipo=m.fkTipo,
                    fkOwner=m.fkOwner,
                    fldDTimeCreateTime=m.fldDTimeCreateTime,
                    fldSStatus=m.fldSStatus,
                    fldNProgress=m.fldNProgress,
                    movements=m.movements,
                    devices=devices,
                    versions=[],
                    dispositivos=dispositivos,
                    imagen="",
                    video="",
                    tuyo=(m.fkOwner == user),
                    fldBRegresivo=m.fldBRegresivo,
                    fldFMinValor=0,
                    fldFMaxValor=0,
                    fldSNomValor=0,
                    fldSToken=m.fldSToken)
    db.execute("""insert into tbl_consultas (fkModel) VALUES (""" + str(mod.id) + """)""")
    db.commit()
    return mod


@router.get("/stadistics/{id}", response_model=List[schemas.ModelStadisticsSensor])
def read_model_stadistics(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (model.fldBPublico == 1)):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    sensores = db.query(tbl_dispositivo_sensor).filter(tbl_dispositivo_sensor.fkOwner == model.id).all()
    version = db.query(tbl_version_estadistica).filter(tbl_version_estadistica.fkOwner == model.id).order_by(
        desc(tbl_version_estadistica.fecha)).first()
    res = []
    for sensor in sensores:
        datos = db.query(datos_estadistica).filter(datos_estadistica.fkVersion == version.id).filter(
            datos_estadistica.fkSensor == sensor.id).order_by(datos_estadistica.fldNSample).all()
        datalist = []
        for dato in datos:
            datalist.append(ModelStadistics(sample=dato.fldNSample, media=dato.fldFMedia, std=dato.fldFStd))
        tiposensor = db.query(tbl_tipo_sensor).get(sensor.fkSensor)
        res.append(
            ModelStadisticsSensor(id=sensor.id, nombre=tiposensor.fldSNombre, datos=datalist, idPosicion=tiposensor.id))
    return res


@router.get("/imagestadistics/{id}", response_model=List[schemas.ModelStadisticsSensor])
def read_model_stadistics_image(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """

    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (model.fldBPublico == 1)):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    sensores = db.query(tbl_dispositivo_sensor).filter(tbl_dispositivo_sensor.fkOwner == model.id).filter(tbl_dispositivo_sensor.fkPosicion == 0).all()
    version = db.query(tbl_version_estadistica).filter(tbl_version_estadistica.fkOwner == model.id).order_by(
        desc(tbl_version_estadistica.fecha)).first()
    res = []
    for sensor in sensores:
        datos = db.query(datos_estadistica).filter(datos_estadistica.fkVersion == version.id).filter(
            datos_estadistica.fkSensor == sensor.id).order_by(datos_estadistica.fldNSample).all()
        datalist = []
        for dato in datos:
            datalist.append(ModelStadistics(sample=dato.fldNSample, media=dato.fldFMedia, std=dato.fldFStd))
        tiposensor = db.query(tbl_tipo_sensor).get(sensor.fkSensor)
        res.append(
            ModelStadisticsSensor(id=sensor.id, nombre=tiposensor.fldSNombre, datos=datalist, idPosicion=tiposensor.id))
    return res


@router.get("/capturas/{id}", response_model=schemas.MovementCaptures)
def count_captures(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Devuelve el numero de capturas de 'Movement' y de 'Other'
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (
            model.fldBPublico == 1
    )):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    movements = db.query(tbl_movement).filter(tbl_movement.fkOwner == model.id).all()
    captures1 = db.query(tbl_capture).filter(tbl_capture.fkOwner == movements[0].id).all()
    captures2 = db.query(tbl_capture).filter(tbl_capture.fkOwner == movements[1].id).all()
    res = MovementCaptures(movement=len(captures1), other=len(captures2))
    return res


@router.put("/", response_model=schemas.Model)
def update_model(
        *,
        id: int,
        db: Session = Depends(deps.get_db),
        model_in: schemas.ModelUpdate,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id)):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    modelRes = crud.model.update(db, db_obj=model, obj_in=model_in)
    movement = db.query(tbl_movement).filter(tbl_movement.fldSLabel != "Other").filter(tbl_movement.fldSLabel != "other").filter(tbl_movement.fkOwner == id).first()
    movement.fldSLabel = modelRes.fldSName
    movement.fldSDescription = modelRes.fldSName
    db.commit()
    return modelRes


@router.get("/categorias/")
def read_categorias(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve models.
    """
    return (db.query(tbl_categorias)
            .offset(skip)
            .limit(limit)
            .all())


@router.get("/captures_resumen/{id}")
def resumen_captures(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Devuelve una lista resumen de capturas
    """
    model = crud.model.get(db=db, id=id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (model.fkOwner == current_user.id) or (
            crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id))):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    movements = db.query(tbl_movement).filter(tbl_movement.fkOwner == model.id).all()
    captures = db.query(tbl_capture).filter(
        or_(tbl_capture.fkOwner == movements[0].id, tbl_capture.fkOwner == movements[1].id)).all()
    res = []
    for capture in captures:
        if capture.fkOwner == movements[0].id:
            res.append(CaptureResumen(nombre=movements[0].fldSLabel, correcto=1, fecha=capture.fldDTimeCreateTime,
                                      id=capture.id))
        else:
            res.append(CaptureResumen(nombre=movements[1].fldSLabel, correcto=0, fecha=capture.fldDTimeCreateTime,
                                      id=capture.id))
    return res[::-1]
