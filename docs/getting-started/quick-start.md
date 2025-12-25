# Quick Start Guide

Get the Server Building Dashboard running in 5 minutes using Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd server-building-dashboard
```

## Step 2: Configure Environment

```bash
# Copy frontend/Docker Compose environment
cp .env.example .env

# Copy backend environment
cd backend
cp .env.example .env
cd ..
```

## Step 3: Start Services

```bash
# Start all services (frontend + backend + MySQL)
./docker.sh prod start
```

Wait for all services to be healthy (usually 30-60 seconds).

## Step 4: Access the Application

Open your browser and navigate to:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000/api |
| API Docs (dev only) | http://localhost:8000/api/docs |

## Step 5: First Login

In development mode (`VITE_DEV_MODE=true`):
1. Click the "Dev Mode" toggle on the login page
2. You'll be logged in as `dev@example.com`

In production mode:
1. Click "Login with SAML"
2. Authenticate with your identity provider
3. You'll be redirected back to the dashboard

## Common Commands

```bash
# View logs
./docker.sh logs -f

# Stop all services
./docker.sh stop

# Restart services
./docker.sh restart

# Rebuild after code changes
./docker.sh prod rebuild

# Start development environment (with hot-reload)
./docker.sh dev start
```

## Verify Installation

### Check Service Health

```bash
# Check all containers are running
docker ps

# Expected output shows 3 containers:
# - server-dashboard-frontend
# - server-dashboard-backend
# - server-dashboard-mysql
```

### Test API Endpoint

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","timestamp":"2025-01-01T00:00:00","version":"1.0.0"}
```

### Test Frontend

Open http://localhost:8080 in your browser. You should see the login page.

## Development Mode Setup

For frontend-only development with hot reload:

```bash
# Install dependencies
npm install

# Start Vite dev server
npm run dev

# Frontend available at http://localhost:5173
```

Edit `.env` to set `VITE_DEV_MODE=true` for mock data.

## Troubleshooting

### Containers not starting?

```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :8080
lsof -i :8000
lsof -i :3306

# View detailed logs
docker compose logs -f
```

### Backend not connecting to MySQL?

```bash
# Wait for MySQL to be fully ready
docker compose logs mysql

# Check MySQL is accepting connections
docker exec -it server-dashboard-mysql mysql -u root -p
```

### SAML not working?

1. Ensure `saml_metadata/idp_metadata.xml` exists in the backend directory
2. Check `SAML_ACS_URL` in `backend/.env` is correct
3. See [Authentication Configuration](../security/authentication.md)

## Next Steps

- [Full Installation Options](installation.md) - Local development, hybrid setups
- [Configuration Reference](configuration.md) - All environment variables
- [Architecture Overview](../architecture/README.md) - Understanding the system
- [API Reference](../api/README.md) - API documentation
