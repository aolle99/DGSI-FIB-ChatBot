# app/schemas/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class MessageCreate(BaseModel):
    content: str
    is_user: bool = True


class MessageResponse(BaseModel):
    id: int
    content: str
    is_user: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
