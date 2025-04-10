# app/services/chat_service.py
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


def create_new_conversation(db: Session, user_id: int, title: str = "Nueva conversación"):
    conversation = Conversation(
        title=title,
        user_id=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_or_create_conversation(db: Session, conversation_id: int = None, user_id: int = None):
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation or conversation.user_id != user_id:
            return create_new_conversation(db, user_id)
        return conversation
    else:
        return create_new_conversation(db, user_id)


def save_message(db: Session, conversation_id: int, content: str, is_user: bool):
    message = Message(
        conversation_id=conversation_id,
        content=content,
        is_user=is_user,
        timestamp=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_context(db: Session, conversation_id: int, max_messages: int = 10):
    """Obtiene el contexto de la conversación para usarlo en el modelo de lenguaje"""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.desc())
        .limit(max_messages)
        .all()
    )
    # Invertimos para tener el orden cronológico
    messages.reverse()
    return messages


def get_conversation_with_messages(db: Session, conversation_id: int):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        return None
    return conversation


async def process_message(db: Session, user_id: int, message: str, conversation_id: int = None):
    """Procesa un mensaje y genera una respuesta del chatbot"""
    # Obtener o crear conversación
    conversation = get_or_create_conversation(db, conversation_id, user_id)

    # Guardar mensaje del usuario
    save_message(db, conversation.id, message, True)

    # Obtener contexto de la conversación
    context = get_conversation_context(db, conversation.id)

    # Aquí se conectaría con el servicio externo de chatbot
    # Por ahora, simularemos una respuesta simple
    response = f"Respuesta simulada a: {message}"

    # Guardar respuesta del sistema
    save_message(db, conversation.id, response, False)

    # Actualizar timestamp de la conversación
    conversation.updated_at = datetime.utcnow()
    db.commit()

    return {"response": response, "conversation_id": conversation.id}
