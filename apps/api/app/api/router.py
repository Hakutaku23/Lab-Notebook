from fastapi import APIRouter

from app.api.routes.attachments import router as attachments_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.records import router as records_router
from app.api.routes.templates import router as templates_router
from app.api.routes.versions import router as versions_router

router = APIRouter()

router.include_router(health_router, tags=["system"])
router.include_router(templates_router, prefix="/templates", tags=["templates"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(records_router, prefix="/records", tags=["records"])
router.include_router(attachments_router, tags=["attachments"])
router.include_router(versions_router, tags=["versions"])