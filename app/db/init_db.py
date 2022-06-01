from typing import List

from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db import base  # noqa: F401

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
from schemas import DeviceCreate


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = schemas.UserCreate(
            full_name='Admin',
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841

    position = crud.position.get_multi(db=db)
    if not position:
        # initial positions
        position_in = schemas.position.PositionCreate(
            name='knee_left',
            description='rodilla izquierda '
        )
        crud.position.create(db=db, obj_in=position_in)
        position_in = schemas.position.PositionCreate(
            name='knee_right',
            description='rodilla derecha '
        )
        crud.position.create(db=db, obj_in=position_in)
        position_in = schemas.position.PositionCreate(
            name='back_lower',
            description='parte baja de la espalda'
        )
        crud.position.create(db=db, obj_in=position_in)

    models = crud.model.get_multi_by_owner(db=db, owner_id=user.id)
    if len(models) == 0:
        devices: List[DeviceCreate] = []
        devices_in = schemas.device.DeviceCreate(
            number_device=1,
            position_id=1
        )
        devices.append(devices_in)
        devices_in = schemas.device.DeviceCreate(
            number_device=2,
            position_id=2
        )
        devices.append(devices_in)

        devices_in = schemas.device.DeviceCreate(
            number_device=3,
            position_id=3
        )
        devices.append(devices_in)

        model_in = schemas.model.ModelCreate(name="sentadillas", description="sentadillas de dos segundos con tres dispositivos",
                                             duration=2, url="", image="", devices=devices)
        model = crud.model.create_with_owner(db=db, obj_in=model_in, owner_id=user.id)

    models = crud.model.get_multi_by_owner(db=db, owner_id=user.id)
    movements = crud.movement.get_all_by_owner(db=db, models=models)
    if len(movements) == 0:
        movement_in = schemas.movement.MovementCreate(label="correcto", description="movimiento realizado correctamente")
        crud.movement.create_with_owner(db=db, obj_in=movement_in, owner_id=models[0].id)
        movement_in = schemas.movement.MovementCreate(label="incorrecto", description="movimiento incorrecto")
        crud.movement.create_with_owner(db=db, obj_in=movement_in, owner_id=models[0].id)
