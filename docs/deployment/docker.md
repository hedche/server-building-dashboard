# Docker Deployment

Complete guide for deploying with Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd server-building-dashboard

# Copy environment files
cp .env.example .env
cd backend && cp .env.example .env && cd ..

# Start production stack
./docker.sh prod start
```

## Docker Management Script

The `docker.sh` script provides convenient commands:

```bash
./docker.sh <environment> <command>
```

### Environments

| Environment | Compose File | Purpose |
|-------------|--------------|---------|
| `prod` | docker-compose.yml | Production deployment |
| `dev` | docker-compose.dev.yml | Development with hot-reload |

### Commands

| Command | Description |
|---------|-------------|
| `start` | Start all services |
| `stop` | Stop all services |
| `restart` | Restart all services |
| `rebuild` | Stop, rebuild, and start |
| `logs` | View logs (`-f` to follow) |
| `help` | Show help |

### Examples

```bash
# Start production
./docker.sh prod start

# Start development
./docker.sh dev start

# View logs (follow)
./docker.sh logs -f

# Rebuild after code changes
./docker.sh prod rebuild

# Stop all services
./docker.sh stop
```

## Docker Compose Files

### Production (docker-compose.yml)

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: server-dashboard-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    deploy:
      resources:
        limits:
          memory: 1G

  backend:
    build: ./backend
    container_name: server-dashboard-backend
    depends_on:
      mysql:
        condition: service_healthy
    environment:
      - ENVIRONMENT=prod
    volumes:
      - ./backend/saml_metadata:/app/saml_metadata:ro
      - ./backend/.env:/app/.env:ro
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  frontend:
    build:
      context: .
      args:
        - VITE_BACKEND_URL=${VITE_BACKEND_URL}
        - VITE_DEV_MODE=false
    container_name: server-dashboard-frontend
    depends_on:
      - backend
    ports:
      - "8080:8080"
```

### Development (docker-compose.dev.yml)

Differences from production:
- `--reload` flag for backend
- Less restrictive security
- Debug logging enabled
- Lower resource limits

## Container Details

### Frontend Container

**Dockerfile:**
```dockerfile
# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_BACKEND_URL
ARG VITE_DEV_MODE=false
RUN npm run build

# Production stage
FROM node:18-alpine
RUN npm install -g serve
COPY --from=build /app/dist /app
USER 1001
EXPOSE 8080
CMD ["serve", "-s", "/app", "-l", "8080"]
```

**Build Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_BACKEND_URL` | Yes | - | Backend API URL |
| `VITE_DEV_MODE` | No | false | Enable dev mode |
| `VITE_APP_NAME` | No | "Server Dashboard" | App name |
| `VITE_LOGIN_LOGO_PATH` | No | - | Custom logo filename |

### Backend Container

**Dockerfile:**
```dockerfile
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y \
    libxmlsec1-dev libxmlsec1-openssl pkg-config
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
RUN apt-get update && apt-get install -y libxmlsec1
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
WORKDIR /app
COPY . .
USER 1000
EXPOSE 8000
CMD ["gunicorn", "main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker"]
```

**Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
```

## Building Images

### Build All Services

```bash
docker compose build
```

### Build Individual Service

```bash
docker compose build frontend
docker compose build backend
```

### Build with No Cache

```bash
docker compose build --no-cache
```

### Build with Custom Tag

```bash
docker build -t myregistry/dashboard-frontend:v1.0 .
docker build -t myregistry/dashboard-backend:v1.0 ./backend
```

## Volume Management

### Named Volumes

```yaml
volumes:
  mysql-data:  # Database persistence
```

### Bind Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `backend/saml_metadata` | `/app/saml_metadata` | SAML IDP metadata |
| `backend/.env` | `/app/.env` | Backend config |
| `backend/tests` | `/app/tests` | Tests (dev only) |

### Volume Commands

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect server-building-dashboard_mysql-data

# Remove all volumes (WARNING: deletes data)
docker compose down -v
```

## Networking

### Default Network

Docker Compose creates a bridge network:

```
server-building-dashboard_app-network
```

### Service Discovery

Containers can reach each other by service name:
- `mysql` → MySQL container
- `backend` → Backend container
- `frontend` → Frontend container

### Port Exposure

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Frontend | 8080 | 8080 |
| Backend | 8000 | 8000 |
| MySQL | 3306 | 3306 (optional) |

## Running Tests

### Backend Tests with Docker

```bash
# Build test image
cd backend
docker build -t server-dashboard-backend-test:latest .

# Run all tests
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v

# Run specific test file
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_auth.py -v

# Run with coverage
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v --cov=app --cov=main --cov-report=term-missing
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs backend

# Check container status
docker ps -a

# Inspect container
docker inspect server-dashboard-backend
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8080

# Use different port
FRONTEND_PORT=8081 docker compose up
```

### Permission Denied

```bash
# Check file permissions
ls -la backend/.env

# Fix permissions
chmod 644 backend/.env
```

### Out of Disk Space

```bash
# Clean up
docker system prune -a

# Remove unused volumes
docker volume prune
```

### MySQL Connection Issues

```bash
# Wait for MySQL to be ready
docker compose logs mysql

# Test connection
docker exec -it server-dashboard-mysql mysql -u root -p
```

## Production Tips

1. **Use specific image tags** instead of `:latest`
2. **Set resource limits** to prevent runaway containers
3. **Enable health checks** for automatic recovery
4. **Use secrets** instead of environment files
5. **Configure logging drivers** for log aggregation
6. **Set up monitoring** with Prometheus/Grafana

## Next Steps

- [Production Guide](production.md) - Production checklist
- [Nginx Guide](nginx.md) - Reverse proxy setup
- [Configuration](../getting-started/configuration.md) - Environment variables
