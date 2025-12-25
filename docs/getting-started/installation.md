# Installation Guide

This guide covers all installation methods for the Server Building Dashboard.

## Installation Methods

| Method | Best For | Requirements |
|--------|----------|--------------|
| [Docker Compose](#docker-compose-recommended) | Production, quick start | Docker, Docker Compose |
| [Local Development](#local-development) | Active development | Node.js, Python |
| [Hybrid Setup](#hybrid-setup) | Frontend dev with Docker backend | Node.js, Docker |

---

## Docker Compose (Recommended)

The easiest way to run the complete stack.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Production Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd server-building-dashboard

# 2. Create environment files
cp .env.example .env
cd backend && cp .env.example .env && cd ..

# 3. Configure environment variables
# Edit .env and backend/.env as needed

# 4. Start production stack
./docker.sh prod start
```

### Development Setup (Hot Reload)

```bash
# Start development stack with hot reload
./docker.sh dev start
```

**Differences from production:**
- Backend runs with `--reload` flag
- Lower resource limits
- Debug logging enabled
- Less restrictive security settings

### Docker Compose Commands

```bash
# Start services
./docker.sh prod start
./docker.sh dev start

# Stop services
./docker.sh stop

# Restart services
./docker.sh restart

# Rebuild and restart (after code changes)
./docker.sh prod rebuild

# View logs
./docker.sh logs -f

# View help
./docker.sh help
```

### Service URLs

| Environment | Frontend | Backend | MySQL |
|-------------|----------|---------|-------|
| Production | :8080 | :8000 | :3306 |
| Development | :8080 | :8000 | :3306 |

---

## Local Development

Run services directly on your machine for maximum development flexibility.

### Frontend Setup

**Prerequisites:**
- Node.js 18+
- npm 9+

```bash
# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Edit .env:
#   VITE_DEV_MODE=true
#   VITE_BACKEND_URL=http://localhost:8000

# 3. Start development server
npm run dev

# Frontend available at http://localhost:5173
```

**Available Scripts:**

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with hot reload |
| `npm run build` | Build production bundle |
| `npm run preview` | Preview production build locally |
| `npm run typecheck` | Run TypeScript type checking |
| `npm run lint` | Run ESLint |

### Backend Setup

**Prerequisites:**
- Python 3.11+
- pip
- (Optional) MySQL 8.0+

```bash
cd backend

# Option A: Automated setup
./setup_script.sh

# Option B: Manual setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Create SAML metadata directory
mkdir -p saml_metadata
# Copy your IDP metadata to saml_metadata/idp_metadata.xml

# 4. Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Backend available at http://localhost:8000
```

**Available Commands:**

| Command | Description |
|---------|-------------|
| `uvicorn main:app --reload` | Start with hot reload |
| `pytest` | Run test suite |
| `pytest -v --cov` | Run tests with coverage |
| `black .` | Format code |
| `ruff check .` | Lint code |

### Running Both Services

Open two terminal windows:

**Terminal 1 - Frontend:**
```bash
npm run dev
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

---

## Hybrid Setup

Run frontend locally with Docker-based backend.

### Setup

```bash
# 1. Start backend with Docker
cd backend
docker compose up -d

# 2. Configure frontend
cd ..
cp .env.example .env
# Edit .env:
#   VITE_BACKEND_URL=http://localhost:8000
#   VITE_DEV_MODE=false  # Use real backend

# 3. Start frontend locally
npm install
npm run dev
```

This gives you:
- Hot reload for frontend development
- Stable, containerized backend
- No Python setup required

---

## Database Setup

### Using Docker MySQL (Recommended)

The Docker Compose setup includes MySQL automatically. No additional setup required.

### Using External MySQL

1. Install MySQL 8.0+
2. Create database and user:

```sql
CREATE DATABASE server_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dashboard_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON server_dashboard.* TO 'dashboard_user'@'%';
FLUSH PRIVILEGES;
```

3. Configure `backend/.env`:

```env
DATABASE_URL=mysql+aiomysql://dashboard_user:your_password@localhost:3306/server_dashboard
```

### Running Without Database

The backend works without a database connection, using mock data:

```env
# In backend/.env
DATABASE_URL=  # Leave empty for mock data
```

---

## SAML Configuration

For production SAML authentication:

1. Obtain IDP metadata from your identity provider (Azure AD, ADFS, etc.)
2. Save to `backend/saml_metadata/idp_metadata.xml`
3. Configure `backend/.env`:

```env
SAML_METADATA_PATH=./saml_metadata/idp_metadata.xml
SAML_ACS_URL=https://your-domain.com/api/auth/callback
```

See [Authentication Configuration](../security/authentication.md) for detailed setup.

---

## Verifying Installation

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend (should return HTML)
curl http://localhost:8080

# MySQL (via Docker)
docker exec server-dashboard-mysql mysqladmin ping -h localhost
```

### Expected Responses

**Backend Health:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "version": "1.0.0"
}
```

**Configuration Endpoint:**
```bash
curl http://localhost:8000/api/config
# Returns region and build server configuration
```

---

## Next Steps

- [Configuration Reference](configuration.md) - All environment variables
- [Development Guide](../development/README.md) - Development workflow
- [Deployment Guide](../deployment/README.md) - Production deployment
