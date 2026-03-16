from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check():
    return {
        "status": "ok",
        "service": "lab-notebook-api"
    }


@router.get("/health/db", summary="Database health check")
def db_health_check():
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected"
    }