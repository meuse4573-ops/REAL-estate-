"""
Core configuration settings for DealMind AI.
All settings are loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dealmind"
    
    # Auth
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # GLM 5.1 Model Configuration
    GLM_API_KEY: str = ""
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    GLM_MODEL: str = "glm-5"
    
    # Gmail OAuth
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/emails/callback/gmail"
    
    # Outlook OAuth
    OUTLOOK_CLIENT_ID: str = ""
    OUTLOOK_CLIENT_SECRET: str = ""
    OUTLOOK_REDIRECT_URI: str = "http://localhost:8000/emails/callback/outlook"
    
    # CRM
    FOLLOWUPBOSS_API_KEY: Optional[str] = None
    
    # Notifications
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # App
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50_000_000  # 50MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()