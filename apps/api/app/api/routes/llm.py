from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.llm import LLMGenerateIn, LLMGenerateOut, LLMStatusOut
from app.services.llm import get_llm_service

router = APIRouter()


@router.get("/status", response_model=LLMStatusOut)
def read_llm_status(current_user: User = Depends(get_current_user)):
    service = get_llm_service()
    return service.status()


@router.post("/generate", response_model=LLMGenerateOut)
def generate_with_llm(payload: LLMGenerateIn, current_user: User = Depends(get_current_user)):
    service = get_llm_service()
    return service.generate(task=payload.task, prompt=payload.prompt, context=payload.context)
