# app/api/endpoints/conversations.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.db.models import User, Conversation
from app.core.schemas import ConversationListResponse, ConversationResponse, ConversationCreate, ConversationUpdate

router = APIRouter()


@router.get("/", response_model=List[ConversationListResponse])
async def get_conversations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Obtener todas las conversaciones del usuario"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return conversations


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
        conversation: ConversationCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Crear una nueva conversación"""
    db_conversation = Conversation(
        title=conversation.title,
        user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
        conversation_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Obtener una conversación específica con sus mensajes"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
        conversation_id: int,
        conversation_update: ConversationUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Actualizar el título de una conversación"""
    db_conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    db_conversation.title = conversation_update.title
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.delete("/{conversation_id}")
async def delete_conversation(
        conversation_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Eliminar una conversación"""
    db_conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    db.delete(db_conversation)
    db.commit()
    return {"message": "Conversación eliminada"}