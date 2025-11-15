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
- `SAML_ENTITY_ID`: Your backend domain (e.g., `https://api.yourdomain.com`)
- `SAML_ACS_URL`: Your callback URL (e.g., `https://api.yourdomain.com/auth/callback`)
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
- Health Check: `http://localhost:8000/health`

## Docker Deployment

### Build and Run with Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Build Docker Image Manually

```bash
docker build -t server-dashboard-backend .
docker run -p 8000:8000 \
  -v $(pwd)/saml_metadata:/app/saml_metadata:ro \
  -v $(pwd)/.env:/app/.env:ro \
  server-dashboard-backend
```

## API Endpoints

### Authentication
- `GET /saml/login` - Initiate SAML login
- `POST /auth/callback` - SAML callback handler
- `GET /me` - Get current user info
- `POST /logout` - Logout

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
- `GET /health` - Health check endpoint

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
| `ENVIRONMENT` | Environment (development/production) | No | development |
| `SAML_METADATA_PATH` | Path to IDP metadata XML | Yes | ./saml_metadata/idp_metadata.xml |
| `SAML_ENTITY_ID` | Service Provider entity ID | Yes | - |
| `SAML_ACS_URL` | Assertion Consumer Service URL | Yes | - |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | http://localhost:5173 |
| `FRONTEND_URL` | Frontend application URL | Yes | http://localhost:5173 |
| `SESSION_LIFETIME_SECONDS` | Session lifetime in seconds | No | 28800 (8 hours) |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | No | 60 |
| `RATE_LIMIT_BURST` | Rate limit burst | No | 100 |

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

- [ ] Set `ENVIRONMENT=production` in `.env`
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

- **Entity ID**: Value from `SAML_ENTITY_ID`
- **ACS URL**: Value from `SAML_ACS_URL`
- **Binding**: HTTP-POST
- **NameID Format**: Email address

You may also need to provide SP metadata. Generate it by accessing:
```
https://your-backend-domain.com/saml/metadata
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

The application logs to stdout/stderr. Configure log aggregation for production:

```bash
# View logs in Docker
docker-compose logs -f backend

# Save logs to file
docker-compose logs backend > backend.log
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
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

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .
```

## Troubleshooting

### SAML Authentication Issues

1. **"SAML metadata file not found"**
   - Ensure `saml_metadata/idp_metadata.xml` exists
   - Check file permissions

2. **"SAML authentication failed"**
   - Verify IDP metadata is current
   - Check `SAML_ENTITY_ID` matches IDP configuration
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

## License

[Your License Here]