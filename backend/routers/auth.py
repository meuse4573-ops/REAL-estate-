"""
Authentication routes - Register and Login endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from core.database import get_supabase
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import uuid
from core.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class AgentResponse(BaseModel):
    id: str
    email: str
    name: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new agent user."""
    supabase = get_supabase()
    
    # Check if email already exists
    result = supabase.table("agents").select("id").eq("email", request.email).execute()
    
    if result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new agent
    agent_id = str(uuid.uuid4())
    password_hash = get_password_hash(request.password)
    
    supabase.table("agents").insert({
        "id": agent_id,
        "email": request.email,
        "name": request.name,
        "password_hash": password_hash,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    access_token = create_access_token(data={"sub": request.email, "agent_id": agent_id})
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login an existing agent."""
    supabase = get_supabase()
    
    # Fetch agent by email
    result = supabase.table("agents").select("*").eq("email", request.email).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    agent = result.data[0]
    
    # Verify password
    if not verify_password(request.password, agent["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": agent["email"], "agent_id": agent["id"]})
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=AgentResponse)
async def get_current_user():
    """Get current authenticated agent's profile - placeholder."""
    # This needs JWT verification - placeholder for now
    return AgentResponse(id="", email="", name="")