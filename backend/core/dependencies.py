"""
FastAPI dependencies for authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .security import decode_access_token
from .database import Database
import asyncpg


security = HTTPBearer()


class Agent:
    """Authenticated agent/user model."""
    
    def __init__(self, id: str, email: str, name: str):
        self.id = id
        self.email = email
        self.name = name


async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Agent:
    """
    FastAPI dependency to get current authenticated agent from JWT token.
    
    Raises:
        HTTPException: If token is invalid or agent not found
        
    Returns:
        Agent instance with id, email, and name
    """
    token = credentials.credentials
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    if email is None or not isinstance(email, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch agent from database
    query = """
        SELECT id, email, name 
        FROM agents 
        WHERE email = $1
    """
    row = await Database.fetch_one(query, email)
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return Agent(
        id=str(row["id"]),
        email=row["email"],
        name=row["name"]
    )


async def get_optional_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Agent]:
    """
    Optional authentication - returns None if no valid token provided.
    Useful for endpoints that work with or without auth.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_agent(credentials)
    except HTTPException:
        return None


def create_token_response(agent_id: str, email: str) -> dict:
    """
    Create token response with access and refresh tokens.
    """
    from .security import create_access_token, create_refresh_token
    
    access_token = create_access_token(data={"sub": email, "agent_id": agent_id})
    refresh_token = create_refresh_token(data={"sub": email, "agent_id": agent_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }