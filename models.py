from datetime import UTC, datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, nullable=False, index=True)
    hashed_password: str = Column(String, nullable=False)
    full_name: str | None = Column(String, nullable=True)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: datetime = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    refresh_tokens = relationship("RefreshToken", back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    token: str = Column(String, unique=True, nullable=False, index=True)
    expires_at: datetime = Column(DateTime, nullable=False)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(UTC))
    is_revoked: bool = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")
