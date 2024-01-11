from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models import tbl_model, tbl_capture, tbl_movement, sensores_estadistica, tbl_version_estadistica, \
    datos_estadistica, tbl_user, tbl_dispositivo_sensor, tbl_tipo_sensor, tbl_position
from app.models.tbl_model import tbl_categorias, tbl_compra_modelo, tbl_history, tbl_imagenes
from app.schemas import MovementCreate, Version, Position
from app.schemas.capture import CaptureResumen
from app.schemas.device import DeviceSensor, Device
from app.schemas.model import ModelStadistics, ModelStadisticsSensor, Model
from app.schemas.movement import MovementCaptures

router = APIRouter()


@router.get("/user/", response_model=List[schemas.Model])
def read_models(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        isDevices: int = 1,
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
        if isDevices != 1:
            devices = [d for d in devices if d.fkPosition != 0]
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
                         versions=versions,
                         dispositivos=dispositivos))
    return res


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
                         versions=versions,
                         dispositivos=dispositivos))
    return res


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
    return crud.model.get_multi_market(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )


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
    return crud.model.get_multi_adquiridos(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )


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
    model = crud.model.create_with_owner(db=db, obj_in=model_in, owner_id=current_user.id)
    movement_correct = MovementCreate(fldSLabel=model.fldSName, fldSDescription=model.fldSName)
    crud.movement.create_with_owner(db=db, obj_in=movement_correct, fkOwner=model.id)
    movement_incorrect = MovementCreate(fldSLabel="Other", fldSDescription="Other")
    crud.movement.create_with_owner(db=db, obj_in=movement_incorrect, fkOwner=model.id)
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
    return 1


@router.get("/{id}", response_model=schemas.Model)
def read_model(
        *,
        db: Session = Depends(deps.get_db),
        id: int,
        current_user: models.tbl_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get model by ID.
    """
    m = crud.model.get(db=db, id=id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    if not (crud.user.is_superuser(current_user) or (m.fkOwner == current_user.id) or (m.fldBPublico == 1)):
        raise HTTPException(status_code=400, detail="Not enough permissions")
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
    img = None
    if m.fkImagen is not None:
        imagen = db.query(tbl_imagenes).get(m.fkImagen)
        if imagen:
            img = imagen.data
    vid = None
    if m.fkVideo is not None:
        video = db.query(tbl_imagenes).get(m.fkVideo)
        if video:
            vid = video.data
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
                versions=versions,
                dispositivos=dispositivos,
                imagen=img,
                video=vid)
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
        res.append(ModelStadisticsSensor(id=sensor.id, nombre=tiposensor.fldSNombre, datos=datalist, idPosicion=tiposensor.id))
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
            crud.ejercicio.asigned(db=db, user=current_user.id, model=model.id))):
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
    return res
