from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.models.user import User
from app.schemas.token import TokenResponse
from app.schemas.user import UserLoginRequest, UserRegisterRequest, UserResponse
from app.security.jwt import create_access_token
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=settings.AUTH_RATE_LIMIT_PER_MINUTE, window_seconds=60))],
    summary="Register a new platform user",
)
async def register(
    user_in: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Registers a new investigator/user account with role-based access.
    Passswords are validated and hashed with bcrypt.
    """
    created_user = AuthService.register_user(db, user_in)
    return created_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit(limit=settings.AUTH_RATE_LIMIT_PER_MINUTE, window_seconds=60))],
    summary="Authenticate and obtain JWT access token",
)
async def login(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates user credentials and returns a signed JWT access token.
    Generic error messaging prevents credential/user enumeration.
    """
    user = AuthService.authenticate_user(
        db,
        email=credentials.email,
        password=credentials.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role.value},
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns profile information of the currently authenticated user based on the Bearer token.
    """
    return current_user
