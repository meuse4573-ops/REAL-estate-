"""Core configuration settings for DealMind AI."""
import os


class Settings:
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SECRET_KEY: str = "your-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 14400
    ANTHROPIC_API_KEY: str = ""
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = ""
    APP_ENV: str = "production"
    FRONTEND_URL: str = ""

    def __init__(self):
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.SECRET_KEY)
        self.ALGORITHM = os.getenv("ALGORITHM", self.ALGORITHM)
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "14400"))
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
        self.GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
        self.GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "")
        self.APP_ENV = os.getenv("APP_ENV", "production")
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "")


settings = Settings()