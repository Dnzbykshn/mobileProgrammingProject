"""Chat endpoint backed by the new conversation application service."""
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.rate_limit import limiter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_application_service import ChatApplicationService
from app.services.chat_postprocess_service import ChatPostprocessService

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
@limiter.limit("60/minute")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id) if current_user else None
    service = ChatApplicationService(db)
    handled = await service.handle_message(
        message=chat_request.message,
        conversation_id=chat_request.conversation_id,
        user_id=user_id,
    )
    background_tasks.add_task(
        ChatPostprocessService.run,
        conversation_id=handled["conversation_id"],
        user_id=handled["user_id"],
        new_phase=handled["new_phase"],
        user_message=handled["user_message"],
        gathered_insight=handled["gathered_insight"],
    )
    return handled["response"]
