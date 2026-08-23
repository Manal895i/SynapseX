from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegisterRequest
from app.security.password import hash_password, verify_password


class AuthService:
    """Service handling user registration and credential authentication logic."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return db.scalars(stmt).first()

    @classmethod
    def register_user(cls, db: Session, user_in: UserRegisterRequest) -> User:
        """
        Registers a new user after verifying that the email address is unique.
        """
        normalized_email = user_in.email.lower().strip()
        existing_user = cls.get_by_email(db, normalized_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address is already registered.",
            )

        hashed = hash_password(user_in.password)
        db_user = User(
            full_name=user_in.full_name.strip(),
            email=normalized_email,
            password_hash=hashed,
            role=user_in.role,
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticates a user by email and password.
        Returns None if credentials fail or user is inactive (generic failure handling).
        """
        normalized_email = email.lower().strip()
        user = cls.get_by_email(db, normalized_email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
