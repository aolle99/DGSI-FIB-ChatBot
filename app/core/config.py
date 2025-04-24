# app/core/config.py
import os

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui_cambiame_en_produccion")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/chatbot")
    PROJECT_NAME: str = "Chatbot"
    VERSION: str = "0.0.1"
    PROJECT_DESCRIPTION: str = "API para el chatbot de la FIB"

    class Config:
        env_file = ".env"


settings = Settings()