# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend for the Server Building Dashboard with SAML2 authentication. This application monitors server builds across multiple regions (CBG, DUB, DAL) and provides APIs for build status, server assignment, and preconfig management.

## Development Commands

### Environment Setup
```bash
# Run automated setup script (creates venv, installs deps, generates .env)
./setup_script.sh

# Manual setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server (using gunicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Testing
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output and coverage
pytest -v --cov=app --cov=main --cov-report=term-missing

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests
pytest -m middleware    # Middleware tests

# Run a specific test file
pytest tests/test_models.py

# Run a specific test
pytest tests/test_models.py::TestUser::test_user_creation_valid
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .
```

### Docker
```bash
# Build image
docker build -t server-dashboard-backend .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

## Architecture

### Application Structure

```
backend/
├── main.py                 # FastAPI app initialization, auth endpoints, lifespan management
├── app/
│   ├── auth.py            # SAML authentication logic, session management
│   ├── config.py          # Pydantic settings, SAML configuration builder
│   ├── middleware.py      # Security headers, rate limiting, request logging
│   ├── models.py          # Pydantic models for requests/responses
│   └── routers/
│       ├── build.py       # Build status and history endpoints
│       ├── server.py      # Server details endpoint
│       ├── assign.py      # Server assignment endpoint
│       └── preconfig.py   # Preconfig management endpoints
└── saml_metadata/
    └── idp_metadata.xml   # IDP metadata (not in git, required at runtime)
```

### Key Components

**Authentication Flow** (main.py:80-158, app/auth.py):
1. `/saml/login` - Initiates SAML auth request, redirects to IDP
2. `/auth/callback` - Processes SAML response, creates session, sets HTTP-only cookie
3. `get_current_user()` dependency - Validates session from cookie for protected endpoints
4. Session storage is in-memory (dict) - **must use Redis in production**

**Configuration** (app/config.py):
- Uses `pydantic-settings` for environment variable validation
- Settings loaded from `.env` file with type checking
- `get_saml_settings()` method (config.py:53-132) builds python3-saml config dict
- Parses IDP metadata and merges with SP settings

**Security Middleware** (app/middleware.py):
- `SecurityHeadersMiddleware`: Adds OWASP-recommended headers (CSP, HSTS, etc.)
- `RateLimitMiddleware`: In-memory rate limiting (60/min sustained, 100 burst) - **use Redis for production**
- Rate limits applied per client IP (supports X-Forwarded-For)

**SAML Attribute Mapping** (app/auth.py:119-168):
Microsoft Azure AD/ADFS attributes:
- Email: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
- Given name: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`
- Surname: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`
- Groups: `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`

**Role Determination** (app/auth.py:184-204):
- Based on SAML group membership
- Default groups: `Dashboard-Admins`, `IT-Admins` → admin role
- `Dashboard-Operators`, `IT-Operators` → operator role
- Customize in `_determine_role()` method

**Data Models** (app/models.py):
- All API requests/responses use Pydantic models for validation
- Server model includes: rackID, hostname, dbid, serial_number, percent_built, assigned_status
- BuildStatus/BuildHistory organize servers by region (cbg, dub, dal)

### Current State

**Mock Data**: All routers currently return mock/simulated data. No database implementation exists yet.

**Production Readiness Gaps**:
1. Session storage uses in-memory dict (app/auth.py:18) - replace with Redis
2. Rate limiting uses in-memory dict (app/middleware.py:57) - replace with Redis-based solution
3. No database configured - DATABASE_URL in config is optional/unused
4. SAML IDP metadata must be manually placed at `saml_metadata/idp_metadata.xml`

## Configuration Requirements

### Essential .env Variables
```bash
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
SAML_ENTITY_ID=https://your-backend-domain.com
SAML_ACS_URL=https://your-backend-domain.com/auth/callback
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
```

### SAML Setup
1. Obtain IDP metadata XML from Azure AD or ADFS
2. Place at `saml_metadata/idp_metadata.xml`
3. Register SP with IDP using entity ID and ACS URL from .env
4. Ensure IDP sends required attributes (email minimum)

## Common Tasks

### Adding a New API Endpoint
1. Create/update router in `app/routers/`
2. Define Pydantic models in `app/models.py`
3. Add authentication with `Depends(get_current_user)` if protected
4. Include router in `main.py` with `app.include_router()`

### Modifying Authentication
- SAML settings: `app/config.py:get_saml_settings()`
- Attribute extraction: `app/auth.py:_extract_user_data()`
- Role mapping: `app/auth.py:_determine_role()`
- Session logic: `app/auth.py:SAMLAuth` class

### Adding Middleware
1. Create middleware class in `app/middleware.py`
2. Add to main.py with `app.add_middleware()` (main.py:46-50)
3. Order matters: security headers → rate limiting → CORS

### Switching to Production Storage
1. Install Redis client: `pip install redis`
2. Update `app/auth.py:store_session()` and `get_session()` to use Redis
3. Update `app/middleware.py:RateLimitMiddleware` to use Redis
4. Add `REDIS_URL` to config.py and .env

## API Endpoints

All endpoints except `/saml/login`, `/auth/callback`, `/health`, and root require authentication.

**Auth**: `/saml/login`, `/auth/callback`, `/me`, `/logout`
**Build**: `/api/build-status`, `/api/build-history/{date}`
**Server**: `/api/server-details?hostname={hostname}`
**Assignment**: `/api/assign`
**Preconfig**: `/api/preconfigs`, `/api/push-preconfig`

API docs available at `/api/docs` in development mode only.

## Testing

### Test Structure

The backend uses pytest for comprehensive test coverage:

- **tests/conftest.py**: Shared fixtures including test client, mock users, mock data
- **tests/test_models.py**: Unit tests for Pydantic models (validation, enums, defaults)
- **tests/test_auth.py**: Authentication tests (SAML processing, session management, user extraction)
- **tests/test_middleware.py**: Middleware tests (security headers, rate limiting, CORS)
- **tests/test_api_*.py**: Integration tests for each API router

### Test Fixtures

Key fixtures available in conftest.py:
- `client`: FastAPI TestClient for making HTTP requests
- `authenticated_user`: Creates session with regular user role
- `authenticated_admin`: Creates session with admin role
- `mock_user_data`: Dictionary with mock user data
- `mock_saml_attributes`: Mock SAML response attributes
- `clear_sessions`: Automatically clears sessions before/after each test

### Writing Tests

When adding new features:
1. Add unit tests for new models/functions
2. Add integration tests for new endpoints
3. Test both authenticated and unauthenticated access
4. Test validation and error cases
5. Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.auth`, `@pytest.mark.middleware`

### CI/CD

GitHub Actions workflow (`.github/workflows/backend-tests.yml`) runs on:
- Push to main/develop
- Pull requests to main/develop
- Manual trigger via workflow_dispatch

The workflow includes:
- Test suite on Python 3.11 and 3.12
- Code formatting check (Black)
- Linting (Ruff)
- Security scanning (Bandit, Safety)
- Coverage reporting (Codecov)

## Security Considerations

- HTTP-only cookies prevent XSS access to session tokens
- CORS configured to allow credentials from specific origins
- All passwords/secrets must be in .env (never commit)
- Docker runs as non-root user (UID 1000)
- Security headers prevent common web vulnerabilities
- Rate limiting prevents abuse (adjust limits in .env if needed)
