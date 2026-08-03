import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "FRAGMENT - Adversarial Validation Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default="fragment_super_secret_jwt_key_2026_quant_platform_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000"
    ]
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/fragment_db")
    SQLITE_FALLBACK_URL: str = Field(default="sqlite+aiosqlite:///./fragment.db")
    
    # Cache / Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # OpenRouter API Key (Optional, for executive reports)
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)
    OPENROUTER_MODEL: str = Field(default="google/gemini-2.5-flash")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
