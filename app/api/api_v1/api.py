from fastapi import APIRouter

from app.api.api_v1.endpoints import models, grupoNegativo, login, users, utils, position, captures, movements, devices

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(captures.router, prefix="/capture", tags=["captures"])
api_router.include_router(position.router, prefix="/position", tags=["positions"])
api_router.include_router(grupoNegativo.router, prefix="/grupo", tags=["grupo"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(movements.router, prefix="/movements", tags=["movements"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
