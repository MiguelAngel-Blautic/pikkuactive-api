from fastapi import APIRouter

from app.api.api_v1.endpoints import ejercicios

api_router = APIRouter()
api_router.include_router(ejercicios.router, prefix="/ejercicios", tags=["ejercicios"])
