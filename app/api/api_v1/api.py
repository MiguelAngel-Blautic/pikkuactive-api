from fastapi import APIRouter

from app.api.api_v1.endpoints import series, ejercicios, login, users, utils, asignaciones, planes, entrenamientos, bloques

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(asignaciones.router, prefix="/asignaciones", tags=["asignaciones"])
api_router.include_router(planes.router, prefix="/planes", tags=["planes"])
api_router.include_router(entrenamientos.router, prefix="/entrenamientos", tags=["entrenamientos"])
api_router.include_router(bloques.router, prefix="/bloques", tags=["bloques"])
api_router.include_router(series.router, prefix="/series", tags=["series"])
api_router.include_router(ejercicios.router, prefix="/ejercicios", tags=["ejercicios"])

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
