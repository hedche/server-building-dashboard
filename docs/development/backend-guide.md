# Backend Development Guide

Guide for FastAPI/Python backend development.

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | Latest | Web framework |
| Pydantic | 2.0+ | Data validation |
| SQLAlchemy | 2.0+ | ORM (async) |
| python3-saml | Latest | SAML authentication |
| Uvicorn | Latest | ASGI server |
| Gunicorn | Latest | Process manager |

## Project Structure

```
backend/
├── main.py                 # Application entry point
├── app/
│   ├── __init__.py
│   ├── auth.py             # SAML authentication
│   ├── config.py           # Configuration
│   ├── middleware.py       # Security middleware
│   ├── models.py           # Pydantic models
│   ├── permissions.py      # Access control
│   ├── database.py         # Database setup
│   ├── correlation.py      # Request tracing
│   ├── logger.py           # Logging utilities
│   └── routers/
│       ├── __init__.py
│       ├── build_history.py
│       ├── preconfig.py
│       ├── assign.py
│       ├── server.py
│       ├── buildlogs.py
│       └── config.py
├── tests/
│   ├── conftest.py         # Test fixtures
│   └── test_*.py           # Test modules
├── config/
│   └── config.json         # Region configuration
├── saml_metadata/
│   └── idp_metadata.xml    # SAML IDP metadata
├── requirements.txt        # Dependencies
└── Dockerfile
```

## Getting Started

### Local Setup

```bash
cd backend

# Automated setup
./setup_script.sh

# OR manual setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env as needed

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

```bash
# Build image
docker build -t server-dashboard-backend .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/saml_metadata:/app/saml_metadata:ro \
  server-dashboard-backend
```

## Router Pattern

### Basic Router

```python
# app/routers/example.py
from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_current_user
from ..models import User, ExampleResponse

router = APIRouter()

@router.get("/example")
async def get_example(user: User = Depends(get_current_user)) -> ExampleResponse:
    """Get example data."""
    return ExampleResponse(data="example")
```

### Including Router

```python
# main.py
from app.routers import example

app.include_router(example.router, prefix="/api", tags=["example"])
```

## Pydantic Models

### Request/Response Models

```python
# app/models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class ExampleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    tags: List[str] = []

class ExampleResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    status: str = "active"

class ErrorResponse(BaseModel):
    error: str
    code: int
    detail: Optional[str] = None
```

### Validation

```python
from pydantic import BaseModel, validator
import re

class HostnameRequest(BaseModel):
    hostname: str

    @validator('hostname')
    def validate_hostname(cls, v):
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Invalid hostname format')
        if len(v) > 253:
            raise ValueError('Hostname too long')
        return v
```

## Authentication

### Protected Endpoint

```python
from fastapi import Depends
from ..auth import get_current_user
from ..models import User

@router.get("/protected")
async def protected_endpoint(user: User = Depends(get_current_user)):
    # user is guaranteed to be authenticated
    return {"email": user.email, "regions": user.allowed_regions}
```

### Permission Checking

```python
from fastapi import HTTPException
from ..permissions import check_region_access

@router.get("/region/{region}")
async def get_region_data(
    region: str,
    user: User = Depends(get_current_user)
):
    # Check user has access to this region
    if not user.is_admin and region not in user.allowed_regions:
        raise HTTPException(403, "Access denied to this region")

    return get_data_for_region(region)
```

## Database Operations

### Async Database Session

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from ..database import get_db

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### CRUD Operations

```python
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

async def get_item(db: AsyncSession, item_id: str):
    result = await db.execute(
        select(Item).where(Item.id == item_id)
    )
    return result.scalar_one_or_none()

async def create_item(db: AsyncSession, item: ItemCreate):
    db_item = Item(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def update_item(db: AsyncSession, item_id: str, updates: dict):
    await db.execute(
        update(Item)
        .where(Item.id == item_id)
        .values(**updates)
    )
    await db.commit()
```

## Error Handling

### HTTP Exceptions

```python
from fastapi import HTTPException

# 400 Bad Request
raise HTTPException(400, "Invalid input")

# 401 Unauthorized
raise HTTPException(401, "Authentication required")

# 403 Forbidden
raise HTTPException(403, "Access denied")

# 404 Not Found
raise HTTPException(404, "Resource not found")

# 500 Internal Server Error
raise HTTPException(500, "Internal server error")
```

### Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Middleware

### Custom Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Before request
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # After request
        duration = time.time() - start_time
        response.headers["X-Process-Time"] = str(duration)

        return response

# Add to app
app.add_middleware(CustomMiddleware)
```

## Configuration

### Environment-Based Config

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Server Building Dashboard"
    ENVIRONMENT: str = "dev"
    SECRET_KEY: str
    DATABASE_URL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

### Using Config

```python
from .config import settings

def get_database_url():
    return settings.DATABASE_URL

def is_production():
    return settings.ENVIRONMENT == "prod"
```

## Logging

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Info level
logger.info(f"Processing request for user {email}")

# Warning level
logger.warning(f"Rate limit approaching for {client_ip}")

# Error level
logger.error(f"Database connection failed: {error}")

# With exception
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
```

### Correlation IDs

```python
from .correlation import get_correlation_id

def log_with_correlation(message: str):
    correlation_id = get_correlation_id()
    logger.info(f"[{correlation_id}] {message}")
```

## Testing

### Test Setup

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def authenticated_client(client):
    # Mock authentication
    with patch('app.auth.get_current_user') as mock:
        mock.return_value = User(
            id="test@example.com",
            email="test@example.com",
            is_admin=True,
            allowed_regions=["cbg", "dub", "dal"]
        )
        yield client
```

### Writing Tests

```python
# tests/test_build_status.py
def test_build_status_authenticated(authenticated_client):
    response = authenticated_client.get("/api/build-status")
    assert response.status_code == 200
    data = response.json()
    assert "cbg" in data or "dub" in data or "dal" in data

def test_build_status_unauthenticated(client):
    response = client.get("/api/build-status")
    assert response.status_code == 401
```

### Running Tests

```bash
# Local
pytest -v

# With coverage
pytest -v --cov=app --cov=main --cov-report=term-missing

# Docker
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  server-dashboard-backend-test:latest \
  pytest -v
```

## Code Quality

### Formatting

```bash
# Format with Black
black .

# Check formatting
black --check .
```

### Linting

```bash
# Lint with Ruff
ruff check .

# Auto-fix
ruff check --fix .
```

### Type Checking

```bash
# Check with MyPy
mypy app/
```

## Best Practices

### Do

- Use type hints everywhere
- Validate all input with Pydantic
- Use dependency injection
- Write async code for I/O operations
- Include docstrings
- Log important operations
- Handle errors gracefully

### Don't

- Use `Any` type without reason
- Skip input validation
- Store secrets in code
- Catch exceptions silently
- Use blocking I/O in async handlers
- Trust user input

## Next Steps

- [Frontend Guide](frontend-guide.md) - Frontend development
- [Testing](testing.md) - Complete testing guide
- [Architecture: Backend](../architecture/backend.md) - Architecture details
