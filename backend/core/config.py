"""Core configuration settings for DealMind AI."""
import os

class Settings:
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SECRET_KEY: str = "your-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 14400
    GLM_API_KEY: str = ""
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    GLM_MODEL: str = "glm-4"
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
        self.GLM_API_KEY = os.getenv("GLM_API_KEY", "")
        self.GLM_BASE_URL = os.getenv("GLM_BASE_URL", self.GLM_BASE_URL)
        self.GLM_MODEL = os.getenv("GLM_MODEL", self.GLM_MODEL)
        self.GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
        self.GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
        self.GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "")
        self.APP_ENV = os.getenv("APP_ENV", "production")
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "")

settings = Settings()