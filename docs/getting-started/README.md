# Getting Started

This section covers everything you need to get the Server Building Dashboard up and running.

## Quick Navigation

| Guide | Description | Time |
|-------|-------------|------|
| [Quick Start](quick-start.md) | Get running with Docker in 5 minutes | ~5 min |
| [Installation](installation.md) | All installation methods detailed | ~15 min |
| [Configuration](configuration.md) | Environment variables reference | Reference |

## Prerequisites

### For Docker Deployment (Recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### For Local Development
- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- MySQL 8.0+ (optional, mock data available)

## Fastest Path

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd server-building-dashboard

# 2. Copy environment files
cp .env.example .env
cd backend && cp .env.example .env && cd ..

# 3. Start all services
./docker.sh prod start

# 4. Access the application
open http://localhost:8080
```

## What Gets Installed

When you run the full stack with Docker Compose, you get:

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 8080 | React application served by `serve` |
| Backend | 8000 | FastAPI application with Gunicorn/Uvicorn |
| MySQL | 3306 | Database for persistent storage |

## Development Mode

For frontend development without backend dependencies:

1. Set `VITE_DEV_MODE=true` in `.env`
2. Run `npm run dev`
3. Application uses mock data automatically

See [Installation](installation.md) for all development options.

## Next Steps

1. **First time?** Start with [Quick Start](quick-start.md)
2. **Need specific setup?** See [Installation](installation.md)
3. **Configuring for production?** See [Configuration](configuration.md)
4. **Understanding the system?** See [Architecture Overview](../architecture/README.md)
