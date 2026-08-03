from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.models import router as models_router
from app.api.v1.validations import router as validations_router
from app.api.v1.market import router as market_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(models_router)
api_router.include_router(validations_router)
api_router.include_router(market_router)
api_router.include_router(reports_router)
