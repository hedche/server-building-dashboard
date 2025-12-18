# Server Building Dashboard - Backend

FastAPI backend with SAML2 authentication for the Server Building Dashboard.

## Features

- ✅ SAML2 authentication with Microsoft Azure AD/ADFS
- ✅ Secure session management with HTTP-only cookies
- ✅ Rate limiting and security headers
- ✅ Comprehensive logging and monitoring
- ✅ Mock data endpoints for development
- ✅ Docker containerization with security best practices
- ✅ DevSecOps compliant implementation

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- SAML IDP metadata XML file from your identity provider

## Quick Start

### Option 1: Development Container (Fastest for Developers)

For quick development without installing Python locally:

```bash
# Start the dev container (uses .env.dev automatically)
docker-compose -f docker-compose.dev.yml up
```

That's it! The API will be available at `http://localhost:8000` with hot-reload enabled.

**Note:** The dev instance uses placeholder SAML settings and mock data. For full SAML testing, see the manual setup below.

### Option 2: Manual Setup (Full Control)

### 1. Setup SAML Metadata

Create the SAML metadata directory and place your IDP metadata file:

```bash
mkdir -p saml_metadata
# Copy your IDP metadata XML file to saml_metadata/idp_metadata.xml
```

The `saml_metadata/idp_metadata.xml` file should contain your Microsoft Azure AD or ADFS metadata. You can obtain this from:
- Azure AD: `https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml`
- ADFS: `https://{adfs-server}/FederationMetadata/2007-06/FederationMetadata.xml`

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Important:** Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update these critical settings in `.env`:
- `SECRET_KEY`: Use the generated secret key above
- `SAML_ACS_URL`: Your callback URL (e.g., `https://api.yourdomain.com/api/auth/callback`)
  - Entity ID is automatically derived from this URL (the origin: scheme + host + port)
- `CORS_ORIGINS`: Your frontend URL
- `FRONTEND_URL`: Your frontend application URL

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run Development Server

```bash
# From the backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- Health Check: `http://localhost:8000/api/health`

## Docker Deployment

### Development Instance (Recommended for Developers)

The development instance uses relaxed security settings, verbose logging, and hot-reload for faster iteration:

```bash
# Build and start dev container
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop
docker-compose -f docker-compose.dev.yml down
```

**Dev Instance Features:**
- Hot-reload: Code changes in `app/` and `main.py` automatically restart the server
- Uses `.env.dev` with development-friendly settings
- Debug logging enabled
- Relaxed rate limits (1000/min)
- Extended session lifetime (24 hours)
- CORS enabled for common dev ports

**Quick Start:**
```bash
# One command to start dev backend
docker-compose -f docker-compose.dev.yml up
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- Health Check: `http://localhost:8000/api/health`

### Seeding the Development Database

Once your dev stack is running (via `./docker.sh dev start` or `docker-compose.dev.yml`), seed the database with test data:

```bash
# Seed the database with ~20 test records (clears existing data first)
docker exec server-dashboard-backend-dev python scripts/seed_dev_data.py
```

**Seed script options:**
```bash
# Append more records without clearing existing data
docker exec server-dashboard-backend-dev python scripts/seed_dev_data.py --append

# Generate a custom number of records
docker exec server-dashboard-backend-dev python scripts/seed_dev_data.py --count 50

# Only seed today's data (no historical records from yesterday)
docker exec server-dashboard-backend-dev python scripts/seed_dev_data.py --today-only
```

**What gets seeded:**
- `build_history`: Server builds in various states (installing, complete, failed)
- `based`: Servers with base images installed
- `preconfigs`: Configuration presets for each region (CBG, DUB, DAL)

### Production Deployment

Production instance with security hardening, minimal attack surface, and optimized performance:

```bash
# Build and start production container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Production Features:**
- Non-root user execution
- Read-only filesystem
- Minimal security capabilities
- Proper rate limiting
- Production-grade settings from `.env`

### Build Docker Image Manually

**Development:**
```bash
docker build -t server-dashboard-backend:dev .
docker run -p 8000:8000 \
  -v $(pwd)/app:/app/app:ro \
  -v $(pwd)/main.py:/app/main.py:ro \
  -v $(pwd)/.env.dev:/app/.env:ro \
  -v $(pwd)/saml_metadata:/app/saml_metadata:ro \
  -e ENVIRONMENT=dev \
  server-dashboard-backend:dev \
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
docker build -t server-dashboard-backend:prod .
docker run -p 8000:8000 \
  -v $(pwd)/saml_metadata:/app/saml_metadata:ro \
  -v $(pwd)/.env:/app/.env:ro \
  server-dashboard-backend:prod
```

## API Endpoints

### Authentication
- `GET /api/saml/login` - Initiate SAML login
- `POST /api/auth/callback` - SAML callback handler
- `GET /api/me` - Get current user info
- `POST /api/logout` - Logout

### Build Status
- `GET /api/build-status` - Get current build status
- `GET /api/build-history/{date}` - Get build history for date

### Server Management
- `GET /api/server-details?hostname={hostname}` - Get server details
- `POST /api/assign` - Assign server to customer

### Preconfig Management
- `GET /api/preconfigs` - Get all preconfigs
- `POST /api/push-preconfig` - Push preconfig to depot

### Health
- `GET /api/health` - Health check endpoint

## Security Features

### Headers
- Strict Transport Security (HSTS)
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection

### Rate Limiting
- 100 requests per minute per IP (burst)
- 60 requests per minute sustained
- Configurable via environment variables

### Session Security
- HTTP-only cookies
- Secure flag in production
- Configurable session lifetime
- Server-side session storage

### Container Security
- Non-root user execution
- Read-only filesystem
- Minimal attack surface
- Security capabilities dropped
- Health checks enabled

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Secret key for session signing | Yes | - |
| `ENVIRONMENT` | Environment (dev/prod) | No | dev |
| `SAML_METADATA_PATH` | Path to IDP metadata XML | Yes | ./saml_metadata/idp_metadata.xml |
| `SAML_ACS_URL` | Assertion Consumer Service URL (Entity ID auto-derived) | Yes | - |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | http://localhost:5173 |
| `FRONTEND_URL` | Frontend application URL | Yes | http://localhost:5173 |
| `SESSION_LIFETIME_SECONDS` | Session lifetime in seconds | No | 28800 (8 hours) |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | No | 60 |
| `RATE_LIMIT_BURST` | Rate limit burst | No | 100 |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No | INFO |
| `LOG_DIR` | Directory for log files | No | /var/log/server-building-dashboard |

### SAML Configuration

The backend uses the `python3-saml` library. SAML settings are configured in `app/config.py` and include:

- **Entity ID**: Your service provider identifier
- **ACS URL**: Where SAML responses are sent
- **Attribute Mappings**: Microsoft Azure AD attributes
  - Email: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
  - Given Name: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`
  - Surname: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`
  - Groups: `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`

## Production Deployment

### Checklist

- [ ] Set `ENVIRONMENT=prod` in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Use HTTPS for all URLs
- [ ] Set up proper DNS and SSL certificates
- [ ] Configure your IDP with correct SP metadata
- [ ] Set appropriate `SESSION_LIFETIME_SECONDS`
- [ ] Enable monitoring and logging
- [ ] Use a production-grade session store (Redis)
- [ ] Set up database for persistent storage
- [ ] Configure backup and disaster recovery
- [ ] Implement proper log aggregation
- [ ] Set up alerting for errors and rate limits

### Registering with Identity Provider

Your IDP (Microsoft Azure AD/ADFS) needs the following Service Provider information:

- **Entity ID**: Auto-derived from `SAML_ACS_URL` (origin only, e.g., `https://api.yourdomain.com`)
- **ACS URL**: Value from `SAML_ACS_URL` (e.g., `https://api.yourdomain.com/api/auth/callback`)
- **Binding**: HTTP-POST
- **NameID Format**: Email address

You may also need to provide SP metadata. Generate it by accessing:
```
https://your-backend-domain.com/api/saml/metadata
```
(Note: This endpoint would need to be implemented if required)

### Reverse Proxy Configuration (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Logging

The application uses a comprehensive logging system with separate log files for different components.

### Log Files

All logs are stored in the directory specified by `LOG_DIR` (default: `/var/log/server-building-dashboard`):

| Log File | Purpose | Contents |
|----------|---------|----------|
| `app.log` | Application | General application events and lifecycle |
| `auth.log` | Authentication | Login, logout, and authentication events |
| `api.log` | API Requests | All HTTP requests with timing and status codes |
| `error.log` | Errors | All errors and exceptions with stack traces |
| `security.log` | Security | Security-related events and warnings |

### Log Features

- **Automatic Rotation**: Logs rotate at 10MB with 5 backup files
- **Structured Format**: Timestamp, level, module, function, and message
- **Console Output**: Logs also appear in stdout for Docker/systemd
- **Request Logging**: All API requests logged with duration and status
- **Error Context**: Full exception traces with contextual information

### Development Logging

In development mode (`.env.dev`), logs are written to `./logs/` directory with DEBUG level for more verbose output.

### Production Logging

Configure log aggregation for production:

```bash
# View logs in Docker
docker-compose logs -f backend

# View specific log file
docker exec server-dashboard-backend cat /var/log/server-building-dashboard/app.log

# Tail error log
docker exec server-dashboard-backend tail -f /var/log/server-building-dashboard/error.log

# Save all logs to file
docker-compose logs backend > backend.log
```

### Log Directory Permissions

Ensure the application has write permissions to the log directory:

```bash
# Create log directory
sudo mkdir -p /var/log/server-building-dashboard

# Set ownership (use appropriate user/group)
sudo chown -R appuser:appuser /var/log/server-building-dashboard

# Or make it writable (less secure)
sudo chmod 777 /var/log/server-building-dashboard
```

**Note**: If the application cannot write to `LOG_DIR`, it will automatically fall back to `./logs` in the current directory.

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:00:00.000000",
  "version": "1.0.0"
}
```

### Metrics

Monitor these key metrics:
- Request rate and response times
- Error rates (4xx, 5xx)
- Rate limit hits
- Session creation/expiration
- SAML authentication success/failure

## Development

### Running Tests

The backend includes comprehensive test coverage with unit tests, integration tests, and security checks.

#### Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests only
pytest -m middleware    # Middleware tests only
```

#### Test Coverage

```bash
# Run tests with coverage report
pytest --cov=app --cov=main --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov=main --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_models.py           # Unit tests for Pydantic models
├── test_auth.py             # Authentication and session tests
├── test_middleware.py       # Middleware functionality tests
├── test_api_health.py       # Health and root endpoint tests
├── test_api_build.py        # Build status API tests
├── test_api_server.py       # Server details API tests
├── test_api_assign.py       # Server assignment API tests
└── test_api_preconfig.py    # Preconfig management API tests
```

#### Test Categories

- **Unit Tests** (`-m unit`): Test individual components in isolation
  - Model validation and serialization
  - Utility functions
  - Business logic

- **Integration Tests** (`-m integration`): Test API endpoints end-to-end
  - HTTP request/response handling
  - Authentication flows
  - Data serialization

- **Auth Tests** (`-m auth`): Test authentication and authorization
  - SAML authentication logic
  - Session management
  - User permissions

- **Middleware Tests** (`-m middleware`): Test middleware components
  - Security headers
  - Rate limiting
  - Request logging
  - CORS configuration

#### Continuous Integration

Tests run automatically on GitHub Actions for:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

The CI pipeline includes:
1. **Test Suite**: Run all tests on Python 3.11 and 3.12
2. **Code Quality**: Black formatting and Ruff linting
3. **Security Checks**: Bandit and Safety scans
4. **Coverage Reports**: Uploaded to Codecov

### Code Quality

```bash
# Format code with Black
black .

# Check formatting without changes
black --check .

# Lint code with Ruff
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Run security scan with Bandit
bandit -r app/ main.py

# Check dependency vulnerabilities
safety check
```

## Troubleshooting

### SAML Authentication Issues

1. **"SAML metadata file not found"**
   - Ensure `saml_metadata/idp_metadata.xml` exists
   - Check file permissions

2. **"SAML authentication failed"**
   - Verify IDP metadata is current
   - Check Entity ID (derived from `SAML_ACS_URL` origin) matches IDP configuration
   - Ensure `SAML_ACS_URL` is correct and accessible
   - Review SAML response in logs

3. **"Session expired or invalid"**
   - Check `SESSION_LIFETIME_SECONDS` setting
   - Verify cookie domain settings
   - Ensure time sync between server and client

### CORS Issues

- Verify `CORS_ORIGINS` includes your frontend URL
- Check that credentials are included in frontend requests
- Ensure HTTPS is used in production

### Rate Limiting

- Adjust `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_BURST` as needed
- Implement Redis-based rate limiting for distributed deployments

## Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── auth.py              # SAML authentication logic
│   ├── config.py            # Configuration management
│   ├── middleware.py        # Security middleware
│   ├── models.py            # Pydantic models
│   └── routers/
│       ├── __init__.py
│       ├── assign.py        # Assignment endpoints
│       ├── build.py         # Build status endpoints
│       ├── preconfig.py     # Preconfig endpoints
│       └── server.py        # Server details endpoints
├── saml_metadata/
│   └── idp_metadata.xml     # IDP metadata (not in git)
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker Compose config
└── .env                    # Environment variables (not in git)
```
