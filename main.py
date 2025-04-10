from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import uvicorn
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# Configuración de la base de datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./chatbot.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Modelos de la base de datos
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    is_user = Column(Integer)  # 1 para mensajes del usuario, 0 para mensajes del bot
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)


# Definición de modelos de datos para la API
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int


class MessageModel(BaseModel):
    id: int
    is_user: bool
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True


class ConversationModel(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageModel] = []

    class Config:
        orm_mode = True


class ConversationCreate(BaseModel):
    title: str


# Configuración de seguridad
SECRET_KEY = "CLAVE_SECRETA_CAMBIAR_EN_PRODUCCION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Funciones de seguridad
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API de Chatbot",
    description="Una API para procesar mensajes de chat con sistema de usuarios",
    version="0.2.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


# Rutas de autenticación y usuarios
@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# Rutas de conversaciones
@app.post("/conversations", response_model=ConversationModel)
async def create_conversation(
        conv: ConversationCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_conversation = Conversation(title=conv.title, user_id=current_user.id)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@app.get("/conversations", response_model=List[ConversationModel])
async def get_user_conversations(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    return conversations


@app.get("/conversations/{conversation_id}", response_model=ConversationModel)
async def get_conversation(
        conversation_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    return conversation


# Ruta para el chat
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
        request: ChatRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        # Verificar si es una conversación existente o nueva
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            ).first()

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversación no encontrada")
        else:
            # Crear una nueva conversación con el primer mensaje como título
            title = request.message[:50] + "..." if len(request.message) > 50 else request.message
            conversation = Conversation(title=title, user_id=current_user.id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Guardar el mensaje del usuario
        user_message = Message(
            conversation_id=conversation.id,
            is_user=1,
            content=request.message
        )
        db.add(user_message)
        db.commit()

        # Simulación de procesamiento de chatbot (aquí integrarás tu modelo)
        # El procesamiento real se implementará más tarde
        bot_response = f"Has enviado: '{request.message}'. Esta es una respuesta simulada del chatbot."

        # Guardar la respuesta del bot
        bot_message = Message(
            conversation_id=conversation.id,
            is_user=0,
            content=bot_response
        )
        db.add(bot_message)

        # Actualizar la conversación
        conversation.updated_at = datetime.utcnow()
        db.commit()

        return ChatResponse(
            response=bot_response,
            conversation_id=conversation.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento del chat: {str(e)}")


@app.get("/")
async def root():
    return {
        "mensaje": "API de Chatbot con sistema de usuarios. Usa el endpoint /chat para interactuar o ve a /static/index.html para la interfaz."
    }


# Ejecutar la aplicación con uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
