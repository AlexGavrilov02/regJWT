import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db, get_current_user
from database import Base
from models import User, RefreshToken

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def db_session(setup_database):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_register_success(client, db_session):
    response = client.post(
        "/register",
        json={"email": "newuser@test.com", "password": "SecurePass1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client, db_session):
    client.post(
        "/register",
        json={"email": "dup@test.com", "password": "SecurePass1"},
    )
    response = client.post(
        "/register",
        json={"email": "dup@test.com", "password": "AnotherPass1"},
    )
    assert response.status_code == 400


def test_register_weak_password(client):
    response = client.post(
        "/register",
        json={"email": "weak@test.com", "password": "weak"},
    )
    assert response.status_code == 422


def test_login_success(client, db_session):
    client.post(
        "/register",
        json={"email": "loginuser@test.com", "password": "SecurePass1"},
    )
    response = client.post(
        "/login",
        json={"email": "loginuser@test.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db_session):
    client.post(
        "/register",
        json={"email": "pwuser@test.com", "password": "SecurePass1"},
    )
    response = client.post(
        "/login",
        json={"email": "pwuser@test.com", "password": "WrongPass1"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/login",
        json={"email": "noone@test.com", "password": "SecurePass1"},
    )
    assert response.status_code == 401


def test_get_me_success(client, db_session):
    client.post(
        "/register",
        json={"email": "meuser@test.com", "password": "SecurePass1"},
    )
    login_resp = client.post(
        "/login",
        json={"email": "meuser@test.com", "password": "SecurePass1"},
    )
    token = login_resp.json()["access_token"]
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "meuser@test.com"


def test_get_me_no_token(client):
    response = client.get("/me")
    assert response.status_code == 403


def test_get_me_invalid_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


def test_update_me_success(client, db_session):
    client.post(
        "/register",
        json={"email": "updateuser@test.com", "password": "SecurePass1"},
    )
    login_resp = client.post(
        "/login",
        json={"email": "updateuser@test.com", "password": "SecurePass1"},
    )
    token = login_resp.json()["access_token"]
    response = client.put(
        "/me",
        json={"full_name": "Test User"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test User"


def test_refresh_success(client, db_session):
    client.post(
        "/register",
        json={"email": "refreshtoken@test.com", "password": "SecurePass1"},
    )
    login_resp = client.post(
        "/login",
        json={"email": "refreshtoken@test.com", "password": "SecurePass1"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    response = client.post(
        "/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_invalid_token(client):
    response = client.post(
        "/refresh",
        json={"refresh_token": "invalidtoken"},
    )
    assert response.status_code == 401


def test_logout_success(client, db_session):
    client.post(
        "/register",
        json={"email": "logoutuser@test.com", "password": "SecurePass1"},
    )
    login_resp = client.post(
        "/login",
        json={"email": "logoutuser@test.com", "password": "SecurePass1"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    response = client.post(
        "/logout",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 204

    response = client.post(
        "/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401


def test_brute_force_protection(client, db_session):
    client.post(
        "/register",
        json={"email": "bruteuser@test.com", "password": "SecurePass1"},
    )
    for i in range(5):
        client.post(
            "/login",
            json={"email": "bruteuser@test.com", "password": "WrongPass1"},
        )

    response = client.post(
        "/login",
        json={"email": "bruteuser@test.com", "password": "SecurePass1"},
    )
    assert response.status_code == 429