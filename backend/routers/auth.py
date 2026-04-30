"""
Authentication routes - Register and Login endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from core.database import Database
from core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from core.dependencies import create_token_response, get_current_agent
import uuid


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
    refresh_token: str
    token_type: str


class AgentResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: Optional[str] = None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new agent user.
    
    Args:
        request: Registration details (email, name, password)
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    existing = await Database.fetch_one(
        "SELECT id FROM agents WHERE email = $1",
        request.email
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new agent
    agent_id = str(uuid.uuid4())
    password_hash = get_password_hash(request.password)
    
    await Database.execute_query(
        """
        INSERT INTO agents (id, email, name, password_hash, created_at)
        VALUES ($1, $2, $3, $4, NOW())
        """,
        agent_id, request.email, request.name, password_hash
    )
    
    return create_token_response(agent_id, request.email)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login an existing agent.
    
    Args:
        request: Login credentials (email, password)
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Fetch agent by email
    row = await Database.fetch_one(
        """
        SELECT id, email, name, password_hash 
        FROM agents 
        WHERE email = $1
        """,
        request.email
    )
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return create_token_response(str(row["id"]), row["email"])


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New JWT access and refresh tokens
    """
    from core.security import decode_access_token
    
    payload = decode_access_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    email = payload.get("sub") or ""
    agent_id = payload.get("agent_id") or ""
    
    # Verify agent still exists
    agent = await Database.fetch_one(
        "SELECT id FROM agents WHERE id = $1",
        agent_id
    )
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found"
        )
    
    return create_token_response(str(agent_id), str(email))


@router.get("/me", response_model=AgentResponse)
async def get_current_user(agent = Depends(get_current_agent)):
    """Get current authenticated agent's profile."""
    return AgentResponse(
        id=agent.id,
        email=agent.email,
        name=agent.name
    )