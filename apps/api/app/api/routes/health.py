from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("/health", summary="服务健康检查")
def health_check():
    return {
        "status": "ok",
        "service": "lab-notebook-api"
    }


@router.get("/health/db", summary="数据库健康检查")
def db_health_check():
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected"
    }
