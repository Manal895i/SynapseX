from typing import Optional
from pydantic import BaseModel
from app.schemas.user import UserResponse


class TokenResponse(BaseModel):
    """Access token payload returned upon successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded internal JWT claim payload."""
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
