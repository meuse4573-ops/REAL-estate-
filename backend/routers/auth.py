"""Authentication routes - Register and Login endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from core.database import get_supabase
from core.security import get_password_hash, verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
    password_hash = get_password_hash(request.password)
    supabase.table("agents").insert({
        "email": request.email,
        "name": request.name,
        "password_hash": password_hash,
    }).execute()
    access_token = create_access_token(data={"sub": request.email})
    return TokenResponse(access_token=access_token)


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
    return TokenResponse(access_token=access_token)