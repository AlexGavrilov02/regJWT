from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать заглавные буквы")
        if not any(c.islower() for c in v):
            raise ValueError("Пароль должен содержать строчные буквы")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать цифры")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)


class LoginAttemptLimit(BaseModel):
    detail: str = "Слишком много попыток входа. Попробуйте позже."