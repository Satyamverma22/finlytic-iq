# app/copilot/router.py

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import get_llm_provider
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.copilot import service
from app.copilot.schemas import ChatRequest, ChatResponse
from app.core.database import get_db
from app.core.rate_limit import rate_limit_by_user

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_by_user("copilot_chat", 30, 60)),
):
    llm = get_llm_provider()
    try:
        result = await service.send_message(
            db, current_user.id, llm, payload.message, payload.conversation_id
        )
    except service.ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return ChatResponse(**result)