# app/api/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.chat_service import process_message
from app.db.models import User
from schemas import ChatResponse, ChatRequest

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
        chat_request: ChatRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Endpoint para procesar mensajes de chat y obtener respuestas"""
    try:
        result = await process_message(
            db,
            current_user.id,
            chat_request.message,
            chat_request.conversation_id
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar mensaje: {str(e)}")