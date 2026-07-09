# Auth API — REST-сервис аутентификации и авторизации

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Описание

REST API, реализующее полноценную систему аутентификации и авторизации с использованием JWT (JSON Web Tokens). Проект демонстрирует понимание основ безопасности веб-приложений: хэширование паролей, JWT-токены, refresh-механизм, защита от брутфорс-атак.

## 🚀 Возможности

- **Регистрация пользователей** — создание аккаунта с валидацией данных
- **Авторизация (Login)** — проверка учётных данных и выдача токенов
- **Обновление access-токена** — получение новой пары токенов по refresh-токену
- **Управление профилем** — просмотр и редактирование данных пользователя
- **Выход (Logout)** — аннулирование refresh-токена
- **Защита от брутфорс-атак** — ограничение попыток входа
- **Хэширование паролей** — безопасное хранение с помощью bcrypt

## 🛠 Стек технологий

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| Фреймворк | FastAPI | REST API, автодокументация, валидация |
| Язык | Python 3.12+ | Основная реализация |
| БД | SQLite / PostgreSQL | Хранение пользователей и токенов |
| ORM | SQLAlchemy | Работа с базой данных |
| Хэширование | passlib + bcrypt | Безопасное хэширование паролей |
| JWT | python-jose | Генерация и валидация JWT-токенов |
| Тесты | pytest + httpx | Модульное тестирование |

## 📁 Структура проекта

```
.
├── main.py              # Основной файл приложения, эндпоинты API
├── auth.py              # Логика аутентификации: хэширование, JWT
├── security.py          # Защита от брутфорс-атак (rate limiting)
├── config.py            # Конфигурация (секреты, настройки токенов)
├── database.py          # Настройка SQLAlchemy и подключения к БД
├── models.py            # ORM-модели (User, RefreshToken)
├── schemas.py           # Pydantic-схемы для валидации данных
├── requirements.txt     # Зависимости проекта
├── tests/
│   └── test_auth.py     # Модульные тесты
└── README.md            # Документация
```

## 📦 Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd project-6
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-super-secret-key-min-32-chars-long
DATABASE_URL=sqlite:///./auth.db
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
```

> ⚠️ **Важно:** `SECRET_KEY` должен быть минимум 32 символа и уникальным для каждого окружения.

### 5. Запуск приложения

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Сервер запустится на `http://localhost:8000`

## 📖 API Документация

После запуска доступны:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Эндпоинты

#### 1. Регистрация

```http
POST /register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "SecurePass1!"
}
```

**Ответ (201 Created):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": null,
    "is_active": true,
    "created_at": "2026-07-09T14:00:00Z"
}
```

**Ошибки:**
| Код | Описание |
|-----|----------|
| 400 | Email уже зарегистрирован |
| 422 | Неверный формат email или слабый пароль |

---

#### 2. Вход (Login)

```http
POST /login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "SecurePass1!"
}
```

**Ответ (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**Ошибки:**
| Код | Описание |
|-----|----------|
| 401 | Неверный email или пароль |
| 429 | Слишком много попыток входа |

---

#### 3. Обновление токена (Refresh)

```http
POST /refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Ответ (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**Ошибки:**
| Код | Описание |
|-----|----------|
| 401 | Неверный/истёкший/аннулированный refresh-токен |

---

#### 4. Получение профиля (Me)

```http
GET /me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Ответ (200 OK):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2026-07-09T14:00:00Z"
}
```

**Ошибки:**
| Код | Описание |
|-----|----------|
| 401 | Неверный или истёкший токен |
| 403 | Токен не предоставлен |

---

#### 5. Обновление профиля

```http
PUT /me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
    "full_name": "John Updated"
}
```

**Ответ (200 OK):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Updated",
    "is_active": true,
    "created_at": "2026-07-09T14:00:00Z"
}
```

---

#### 6. Выход (Logout)

```http
POST /logout
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Ответ (204 No Content)** — успешно, тело ответа пустое.

## 🔐 Безопасность

### Хэширование паролей

Пароли хэшируются с помощью **bcrypt** через библиотеку `passlib`:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed = pwd_context.hash("my_secret_password")
is_match = pwd_context.verify("my_secret_password", hashed)
```

- Пароли **никогда не хранятся** в открытом виде
- Используется уникальный salt для каждого пароля
- bcrypt автоматически защищает от перебора (slow hash)

### JWT-токены

| Параметр | Значение | Описание |
|----------|----------|----------|
| `sub` | email пользователя | Subject — идентификатор субъекта |
| `exp` | timestamp | Время истечения токена |
| `type` | access/refresh | Тип токена |
| `jti` | random hex (refresh) | Unique ID для отслеживания refresh-токенов |

**Access-токен:**
- Срок действия: **15 минут** (настраивается)
- Содержит только email пользователя
- Используется для доступа к защищённым ресурсам

**Refresh-токен:**
- Срок действия: **7 дней** (настраивается)
- Хранится в базе данных
- Позволяет получить новый access-токен без повторного входа
- Может быть аннулирован через logout

### Защита от брутфорса

Реализован механизм ограничения попыток входа:

```python
# Конфигурация
MAX_LOGIN_ATTEMPTS = 5      # Максимум попыток
LOCKOUT_DURATION_MINUTES = 15  # Время блокировки
```

После превышения лимита попыток вход блокируется на заданное время.

### HTTP Bearer аутентификация

Защищённые эндпоинты используют `HTTPBearer` — токен передаётся в заголовке:

```
Authorization: Bearer <access_token>
```

## 🧪 Тестирование

### Запуск всех тестов

```bash
pytest tests/ -v
```

### Запуск с покрытием

```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Список тестов

| # | Тест | Что проверяет |
|---|------|---------------|
| 1 | `test_register_success` | Успешная регистрация пользователя |
| 2 | `test_register_duplicate_email` | Отклонение дублирующегося email |
| 3 | `test_register_weak_password` | Валидация сложности пароля |
| 4 | `test_login_success` | Успешный вход и получение токенов |
| 5 | `test_login_wrong_password` | Отклонение неверного пароля |
| 6 | `test_login_nonexistent_user` | Отклонение несуществующего пользователя |
| 7 | `test_get_me_success` | Доступ к профилю с валидным токеном |
| 8 | `test_get_me_no_token` | Блокировка без токена (403) |
| 9 | `test_get_me_invalid_token` | Блокировка с невалидным токеном (401) |
| 10 | `test_update_me_success` | Обновление профиля пользователя |
| 11 | `test_refresh_success` | Обновление токенов по refresh-токену |
| 12 | `test_refresh_invalid_token` | Отклонение невалидного refresh-токена |
| 13 | `test_logout_success` | Аннулирование refresh-токена при выходе |
| 14 | `test_brute_force_protection` | Блокировка после превышения попыток входа |

**Результат:** ✅ 14/14 тестов пройдено

## 📝 Примеры использования (cURL)

### Регистрация

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass1!"}'
```

### Вход

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass1!"}'
```

### Получить профиль

```bash
curl http://localhost:8000/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Обновить токен

```bash
curl -X POST http://localhost:8000/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### Выйти

```bash
curl -X POST http://localhost:8000/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## 🔄 Жизненный цикл токенов

```
┌──────────┐     POST /login      ┌─────────────┐
│          │ ──────────────────►  │ Access: 15m │
│  Client  │                      │ Refresh: 7d │
│          │ ◄──────────────────  └─────────────┘
└──────────┘     Токены

Access токен истёк (15 мин)
       │
       ▼
POST /refresh ──────────────► Новый Access + Refresh
                               (Refresh: 7d)

Logout
       │
       ▼
Refresh аннулирован в БД
```

## ⚙️ Конфигурация

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `SECRET_KEY` | — | Секретный ключ для подписи JWT (мин. 32 символа) |
| `DATABASE_URL` | `sqlite:///./auth.db` | URL подключения к БД |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Срок жизни access-токена в минутах |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Срок жизни refresh-токена в днях |
| `MAX_LOGIN_ATTEMPTS` | `5` | Максимум попыток входа |
| `LOCKOUT_DURATION_MINUTES` | `15` | Время блокировки после превышения попыток |

## 🚀 Развёртывание

### Production запуск

```bash
pip install uvicorn[standard]
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### PostgreSQL

Замените `DATABASE_URL` в `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/authdb
```

Установите драйвер:

```bash
pip install psycopg2-binary
```

## 📋 Чек-лист реализации

- [x] Регистрация с валидацией email и пароля
- [x] Хэширование паролей (bcrypt)
- [x] JWT access-токен (15 минут)
- [x] JWT refresh-токен (7 дней)
- [x] Обновление токенов
- [x] Получение профиля пользователя
- [x] Обновление профиля
- [x] Выход (аннулирование токена)
- [x] Защита от брутфорс-атак
- [x] Валидация JWT-токенов
- [x] Обработка истекших токенов
- [x] Модульные тесты (14/14 passed)

