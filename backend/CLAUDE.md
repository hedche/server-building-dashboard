# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend for the Server Building Dashboard with SAML2 authentication. This application monitors server builds across multiple regions (CBG, DUB, DAL) and provides APIs for build status, server assignment, and preconfig management.

## Development Commands

### Environment Setup
```bash
# Copy config files
cp .env.example .env
cp config/config.json.example config/config.json

# Run automated setup script (creates venv, installs deps)
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

**IMPORTANT: Always use Docker for running tests.** The Docker container has all required dependencies (Python 3.11, libxmlsec1 for SAML, etc.) and ensures consistent test results. Do not attempt to run tests locally with venv.

#### Docker Testing (required)

All commands must be run from the `backend/` directory.

```bash
# Build the Docker test image (one-time setup, or after Dockerfile changes)
docker build -t server-dashboard-backend-test:latest .

# Run all tests
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/app:/app/app:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v

# Run all tests with coverage report
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/app:/app/app:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v --cov=app --cov=main --cov-report=term-missing

# Run specific test file
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/app:/app/app:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_lock_service.py -v

# Run specific test by name
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/app:/app/app:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_lock_service.py::TestAcquireLock::test_acquire_lock_no_existing_lock -v

# Run tests by marker
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/app:/app/app:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -m unit -v
```

**Volume mounts explained:**
- `tests:/app/tests:ro` - Test files (read-only)
- `app:/app/app:ro` - Application code (read-only, allows testing local changes)
- `saml_metadata:/app/saml_metadata:ro` - SAML IDP metadata (required for app init)
- `.env.example:/app/.env:ro` - Environment variables (.env.example works for tests)

**Why Docker is required:**
- Ensures Python 3.11 environment
- Includes system dependencies (libxmlsec1 for SAML)
- Matches production container environment
- No need to manage local Python virtual environments
- Consistent results across macOS, Linux, and Windows

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .
```

### Docker

**Note**: Docker Compose files have been moved to the repository root. Use the `docker.sh` script from the root directory to manage the full application stack (frontend + backend + database).

```bash
# From repository root - run full stack
cd ..
./docker.sh prod start      # Start all services
./docker.sh logs -f         # View logs
./docker.sh stop            # Stop all services

# Build backend image only (from backend/ directory)
docker build -t server-dashboard-backend .
```

See the main CLAUDE.md in the repository root for full Docker documentation.

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
1. `/api/saml/login` - Initiates SAML auth request, redirects to IDP
2. `/api/auth/callback` - Processes SAML response, creates session, sets HTTP-only cookie
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
SAML_ACS_URL=https://your-backend-domain.com/api/auth/callback
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
```

Note: Entity ID is automatically derived from `SAML_ACS_URL` (the origin: scheme + host + port).

### SAML Setup
1. Obtain IDP metadata XML from Azure AD or ADFS
2. Place at `saml_metadata/idp_metadata.xml`
3. Register SP with IDP using:
   - Entity ID: Auto-derived from ACS URL origin (e.g., `https://your-backend-domain.com`)
   - ACS URL: Full callback URL from .env
4. Ensure IDP sends required attributes (email minimum)

### Hostname Validation Configuration

The `HOSTNAME_PATTERN` environment variable controls which hostname formats are accepted by the build logs API:

```bash
# Default pattern (flexible - recommended for most deployments)
HOSTNAME_PATTERN=^[a-zA-Z0-9._-]+$

# Strict region-based format
HOSTNAME_PATTERN=^[a-z]{3}-srv-[0-9]{3}$  # Matches: cbg-srv-001, dub-srv-002

# Custom format
HOSTNAME_PATTERN=^[a-z]{2}-[0-9]{5}-[0-9]{2}$  # Matches: th-12345-45
```

**Security Note**: This pattern is used to prevent path traversal attacks in the build logs endpoint. Ensure your custom pattern does not allow dangerous characters like `..`, `/`, `\`, or other path separators.

**Testing**: After changing the pattern, verify it accepts valid hostnames and rejects invalid ones:
```bash
# Test valid hostname
curl http://localhost:8000/api/build-logs/your-test-hostname

# Should return 400 if hostname doesn't match pattern
```

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

## Logging and Debugging

### Log Files

The backend creates separate log files for different components in the `LOG_DIR` directory (default: `/var/log/server-building-dashboard`):

| Log File | Purpose | Key Information |
|----------|---------|-----------------|
| `app.log` | General application logs | Startup, configuration, general events |
| `api.log` | API request/response logs | All HTTP requests, response codes, timing |
| `auth.log` | Authentication events | SAML logins, session management |
| `security.log` | Security events | Rate limiting, unauthorized access |
| `error.log` | Error tracking | All errors and exceptions |
| **`preconfig.log`** | **Preconfig operations** | **Detailed preconfig push debugging** |
| **`build-logs.log`** | **Build log operations** | **Hostname validation, file discovery, read operations** |

**Note**: If the application doesn't have write permission to `LOG_DIR`, it will fall back to `./logs` in the current directory.

### Debug Logging for Preconfig Push

The preconfig push logic includes comprehensive debug-level logging to a dedicated log file (`preconfig.log`). This makes it easy to troubleshoot preconfig pushing issues.

#### Enabling Debug Logging

Set `LOG_LEVEL=DEBUG` in your `.env` file:

```bash
# In backend/.env
LOG_LEVEL=DEBUG
```

Then restart the backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### What Gets Logged at DEBUG Level

When DEBUG logging is enabled, the `preconfig.log` file will contain detailed information about every preconfig push operation:

**1. Request Information**
```
Region: cbg -> Depot: 1
User: user@example.com (Role: operator)
Build servers configured: 2
  - cbg-build-01: handles appliance sizes ['small', 'medium']
  - cbg-build-02: handles appliance sizes ['large', 'xlarge']
```

**2. Lock Acquisition**
```
[LOCK] Acquire lock request: region=cbg, user=user@example.com, timeout=300s
[LOCK] Checking for existing lock on region cbg...
[LOCK] No existing lock found - creating new lock...
[LOCK] ✓ Lock creation successful, expires at 2026-01-28 15:45:00
```

**3. Database Queries**
```
Querying database for preconfigs: depot=1, date=2026-01-28
Found 15 preconfigs to push for depot 1 today
```

**4. Preconfig Details**
```
PRECONFIGS TO PUSH:
  DBID: dbid-001-123        | Depot: 1 | Size: small      | Created: 2026-01-28 10:30:00
  DBID: dbid-001-124        | Depot: 1 | Size: medium     | Created: 2026-01-28 10:31:00
  DBID: dbid-001-125        | Depot: 1 | Size: large      | Created: 2026-01-28 10:32:00

PRECONFIGS BY APPLIANCE SIZE:
  small: 5 preconfig(s)
  medium: 7 preconfig(s)
  large: 3 preconfig(s)
```

**5. Push Operations** (per build server)
```
Processing build server: cbg-build-01
  Server handles appliance sizes: ['small', 'medium']
  Matched 12 preconfigs for this server
  Preconfigs to push to cbg-build-01:
    - DBID: dbid-001-123 | Size: small
    - DBID: dbid-001-124 | Size: medium
  PUT https://cbg-build-01.internal.example.com/preconfig
  Payload size: 12 preconfig(s)
  Timeout: 30s
  ✓ SUCCESS: cbg-build-01 - Status: 200
    Tracked: DBID dbid-001-123 pushed to cbg-build-01
    Tracked: DBID dbid-001-124 pushed to cbg-build-01
```

**6. Database Updates**
```
UPDATING DATABASE WITH PUSH RESULTS
DBID dbid-001-123:
  Previously pushed to: ['cbg-build-03']
  New successful pushes: ['cbg-build-01']
  Updated pushed_to list: ['cbg-build-03', 'cbg-build-01']
  Last pushed at: 2026-01-28 15:30:45.123456+00:00
```

**7. Summary**
```
PUSH OPERATION SUMMARY
Total build servers: 2
  ✓ Successful: 2
  ✗ Failed: 0
  ⊘ Skipped: 0
Total preconfigs processed: 15
Total preconfigs pushed successfully: 15
Overall status: success
Response message: Successfully pushed preconfigs to 2 build server(s)
```

**8. Lock Release**
```
[LOCK] Releasing lock for region cbg...
[LOCK] ✓ Lock deleted successfully
```

#### Reading Preconfig Logs

**Tail the log in real-time:**
```bash
tail -f /var/log/server-building-dashboard/preconfig.log
```

**Search for specific DBIDs:**
```bash
grep "dbid-001-123" /var/log/server-building-dashboard/preconfig.log
```

**See only push summaries:**
```bash
grep "PUSH OPERATION SUMMARY" -A 10 /var/log/server-building-dashboard/preconfig.log
```

**Find failed pushes:**
```bash
grep "✗" /var/log/server-building-dashboard/preconfig.log
```

**View logs for a specific correlation ID** (from X-Request-ID header):
```bash
grep "abc123def456" /var/log/server-building-dashboard/preconfig.log
```

#### Production Logging

In production, set `LOG_LEVEL=INFO` to reduce log volume. INFO level still includes:
- Successful/failed push operations
- Lock acquisition/release events
- Database query results
- Error messages

DEBUG level is verbose and should only be used for troubleshooting.

### Debug Logging for Build Logs

The build logs endpoint includes comprehensive debug-level logging to help troubleshoot issues with log file discovery and access.

#### What Gets Logged at DEBUG Level

When DEBUG logging is enabled, the `build-logs.log` file will contain detailed information:

**1. Request Information**
```
BUILD LOG REQUEST - Hostname: cbg-srv-001
User: user@example.com (Role: operator)
BUILD_LOGS_DIR: /var/log/build-servers
HOSTNAME_PATTERN: ^[a-zA-Z0-9._-]+$
```

**2. Hostname Validation**
```
[BUILDLOG] Validating hostname: 'cbg-srv-001'
[BUILDLOG] Hostname length: 11 characters
[BUILDLOG] ✓ Length check passed (11 chars)
[BUILDLOG] Using pattern: ^[a-zA-Z0-9._-]+$
[BUILDLOG] ✓ Hostname format valid
```

**3. File Discovery**
```
[BUILDLOG] Starting file discovery...
[BUILDLOG] Searching in: /var/log/build-servers
[BUILDLOG] Found 3 build server(s): ['build-server-01', 'build-server-02', 'build-server-03']
[BUILDLOG] Searching for log file...
[BUILDLOG] Checking build server: build-server-01
[BUILDLOG]   Candidate path: /var/log/build-servers/build-server-01/cbg-srv-001/cbg-srv-001-Installer.log
[BUILDLOG]   Resolved path: /var/log/build-servers/build-server-01/cbg-srv-001/cbg-srv-001-Installer.log
[BUILDLOG]   ✓ Path is within BUILD_LOGS_DIR
[BUILDLOG] ✓ Log file found in build server: build-server-01
```

**4. File Operations**
```
[BUILDLOG] File size: 245,890 bytes (0.23 MB)
[BUILDLOG] Size limit: 10,485,760 bytes (10 MB)
[BUILDLOG] ✓ File size within limits
[BUILDLOG] Reading file with UTF-8 encoding...
[BUILDLOG] ✓ File read successful
[BUILDLOG] Content length: 245,890 characters
[BUILDLOG] Content preview (first 100 chars): 2026-01-28 10:30:00 - Starting installation...\n2026-01-28 10:30:01 - Checking dependencies...
```

**5. Response Summary**
```
BUILD LOG RESPONSE SUMMARY
Status: 200 OK
Build Server: build-server-01
File Path: /var/log/build-servers/build-server-01/cbg-srv-001/cbg-srv-001-Installer.log
File Size: 245,890 bytes
Content Type: text/plain; charset=utf-8
X-Build-Server Header: build-server-01
```

#### Reading Build Logs

**Tail the log in real-time:**
```bash
tail -f /var/log/server-building-dashboard/build-logs.log
```

**Search for specific hostname:**
```bash
grep "cbg-srv-001" /var/log/server-building-dashboard/build-logs.log
```

**Find failed validations:**
```bash
grep "✗" /var/log/server-building-dashboard/build-logs.log
```

**See only successful log retrievals:**
```bash
grep "BUILD LOG RESPONSE SUMMARY" -A 7 /var/log/server-building-dashboard/build-logs.log
```

**View logs for a specific correlation ID:**
```bash
grep "abc123def456" /var/log/server-building-dashboard/build-logs.log
```

### Correlation IDs

Every request is assigned a correlation ID (UUID) that appears in all log entries. This makes it easy to trace a specific user's action through all log files:

```
2026-01-28 15:30:45 | INFO     | abc123def456                         | app.preconfig           | push_preconfig       | Push preconfig to region cbg (depot 1) requested by user@example.com
```

The correlation ID is also returned in the `X-Request-ID` response header, allowing frontend debugging.

## API Endpoints

All endpoints except `/api/saml/login`, `/api/auth/callback`, `/api/health`, and `/api` require authentication.

**Auth**: `/api/saml/login`, `/api/auth/callback`, `/api/me`, `/api/logout`
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
