from fastapi import APIRouter

from app.api.api_v1.endpoints import models, login, users, utils, movements, position, captures, test

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(movements.router, prefix="/movement", tags=["movements"])
api_router.include_router(captures.router, prefix="/capture", tags=["captures"])
api_router.include_router(position.router, prefix="/position", tags=["positions"])
api_router.include_router(test.router, prefix="/test", tags=["test"])

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
