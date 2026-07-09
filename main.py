from datetime import UTC, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from config import settings
from database import SessionLocal, init_db
from models import RefreshToken, User
from schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserOut,
)
from security import brute_force_protection

app = FastAPI(title="Auth API", version="1.0.0")
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен")

    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")

    return user


@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    identifier = data.email

    if not brute_force_protection.check_attempt(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток входа. Попробуйте позже.",
        )

    user = db.query(User).filter(User.email == data.email).first()

    if user is None or not verify_password(data.password, user.hashed_password):
        brute_force_protection.record_attempt(identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    brute_force_protection.reset_attempts(identifier)

    access_token = create_access_token({"sub": user.email})
    refresh_token_value = create_refresh_token({"sub": user.email})

    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(user_id=user.id, token=refresh_token_value, expires_at=expires_at)
    db.add(rt)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
    )


@app.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный refresh-токен")

    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")

    stored_rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == data.refresh_token)
        .first()
    )

    if stored_rt is None or stored_rt.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh-токен недействителен")

    expires_at = _ensure_utc(stored_rt.expires_at)
    now = datetime.now(UTC)
    if now > expires_at:
        stored_rt.is_revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh-токен истёк")

    new_access_token = create_access_token({"sub": user.email})
    new_refresh_token_value = create_refresh_token({"sub": user.email})

    stored_rt.is_revoked = True
    db.commit()

    new_expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_rt = RefreshToken(user_id=user.id, token=new_refresh_token_value, expires_at=new_expires_at)
    db.add(new_rt)
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token_value,
    )


@app.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    stored_rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == data.refresh_token)
        .first()
    )

    if stored_rt:
        stored_rt.is_revoked = True
        db.commit()


@app.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.put("/me", response_model=UserOut)
def update_me(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    db.commit()
    db.refresh(current_user)
    return current_user


@app.on_event("startup")
def startup():
    init_db()