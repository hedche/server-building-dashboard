# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **fullstack monorepo** for the Server Building Dashboard - a system for monitoring server builds, managing preconfigurations, and assigning servers across multiple data center regions (CBG, DUB, DAL).

**Technology Stack:**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (at root level)
- **Backend**: Python + FastAPI + SAML2 authentication (in `backend/` directory)

## Monorepo Structure

```
server-building-dashboard/
├── src/                    # Frontend React application
│   ├── components/         # Reusable UI components
│   ├── pages/              # Page components (Overview, Preconfig, Assignment, BuildLogs)
│   ├── hooks/              # Custom React hooks for API calls
│   ├── contexts/           # React contexts (AuthContext)
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── App.tsx             # Main app component with routing
│   └── main.tsx            # Application entry point
├── backend/                # Python FastAPI backend
│   ├── app/                # FastAPI application code
│   │   ├── routers/        # API route handlers (build, server, assign, preconfig)
│   │   ├── auth.py         # SAML authentication logic
│   │   ├── config.py       # Configuration management
│   │   ├── middleware.py   # Security headers, rate limiting
│   │   └── models.py       # Pydantic models
│   ├── tests/              # Pytest test suite
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend Docker build
│   ├── docker-compose.yml  # Backend Docker Compose
│   └── CLAUDE.md           # Detailed backend documentation
├── vite.config.ts          # Vite build configuration
├── tsconfig.json           # TypeScript configuration
├── tsconfig.app.json       # TypeScript app-specific config
├── package.json            # Frontend dependencies (npm)
├── index.html              # Frontend entry HTML
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
├── eslint.config.js        # ESLint configuration
├── Dockerfile              # Frontend Docker build
└── nginx.conf              # Nginx config for frontend serving

**Why this structure?**
- Frontend at root follows standard Vite/React conventions (configs expect root-level `src/`)
- Backend in subdirectory keeps Python code isolated and independently deployable
- This is a common monorepo pattern for fullstack applications
```

## Quick Start

### Docker (Easiest - Full Stack)

Run the entire application stack (frontend + backend + database) with one command:

```bash
# 1. Copy environment and config files
cp .env.example .env
cd backend
cp .env.example .env
cp config/config.json.example config/config.json
cd ..

# 2. Start all services
./docker.sh prod start

# Services will be available at:
# - Frontend: http://localhost:8080
# - Backend API: http://localhost:8000
# - Database: localhost:3306
```

For development with hot-reload:
```bash
./docker.sh dev start
```

### Frontend Development (Local)

```bash
# Install dependencies
npm install

# Start development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Type check without building
npm run typecheck

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Automated setup (creates venv, installs deps, generates .env)
./setup_script.sh

# OR manual setup:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start development server (http://localhost:8000)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests (local with venv - requires dependencies installed)
pytest

# Run tests with coverage
pytest -v --cov=app --cov=main --cov-report=term-missing
```

**Testing with Docker (Recommended)**

Docker testing ensures a consistent environment and matches the production build:

```bash
# From the backend/ directory

# 1. Build the Docker test image
docker build -t server-dashboard-backend-test:latest .

# 2. Run all tests
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v

# 3. Run specific test file (e.g., authentication tests)
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_auth.py -v

# 4. Run tests with coverage report
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v --cov=app --cov=main --cov-report=term-missing

# 5. Run specific test by name
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_auth.py::TestSAMLAuth::test_extract_user_data -v
```

**Why use Docker for testing?**
- Ensures consistent Python environment (3.11) across all machines
- Includes all system dependencies (libxmlsec1, etc.) needed for SAML
- Matches the production container environment
- No need to manage local Python virtual environments
- Works the same on macOS, Linux, and Windows

**Volume Mounts Explained:**
- `tests:/app/tests:ro` - Mounts your local tests directory (read-only)
- `saml_metadata:/app/saml_metadata:ro` - SAML IDP metadata required for app initialization
- `.env.example:/app/.env:ro` - Environment variables for tests (.env.example works for testing)
```

### Fullstack Development

Run both servers simultaneously:

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Development Workflow

### Frontend Development Mode

When `VITE_DEV_MODE=true` in `.env`:
- No SAML authentication required
- Mock data used for all API calls
- Automatic login as test user (`dev@example.com`)
- Yellow "Dev Mode" button appears in bottom-right corner
- Perfect for frontend work without backend dependencies

### Production Mode

When `VITE_DEV_MODE=false`:
- Full SAML authentication flow
- Real API calls to backend at `VITE_BACKEND_URL`
- HTTP-only cookies for session management
- Backend must be running with proper SAML configuration

## Architecture Integration

### Frontend ↔ Backend Communication

- **Base URL**: Frontend uses `VITE_BACKEND_URL` environment variable
- **Authentication**: SAML2 in production, mock in dev mode
- **Session Management**: HTTP-only cookies (secure, prevents XSS)
- **CORS**: Backend allows frontend origin with credentials
- **API Format**: JSON requests/responses with Pydantic validation

### Key Integration Points

1. **Authentication Flow** (src/contexts/AuthContext.tsx ↔ backend/main.py:80-158):
   - `/api/saml/login` - Initiates SAML auth
   - `/api/auth/callback` - Processes SAML response, creates session
   - `/api/me` - Gets current user info from session
   - `/api/logout` - Destroys session

2. **Build Status** (src/hooks/useBuildStatus.ts ↔ backend/app/routers/build.py):
   - `GET /api/build-status` - Current builds by region
   - `GET /api/build-history/{date}` - Historical builds

3. **Server Management** (src/hooks/useServerDetails.ts ↔ backend/app/routers/server.py):
   - `GET /api/server-details?hostname={hostname}` - Detailed server info

4. **Preconfig Management** (src/pages/Preconfig.tsx ↔ backend/app/routers/preconfig.py):
   - `GET /api/preconfigs` - List all preconfigs
   - `POST /api/push-preconfig` - Push config to depot

5. **Server Assignment** (src/pages/Assignment.tsx ↔ backend/app/routers/assign.py):
   - `POST /api/assign` - Assign server to customer

### API Contracts

All API endpoint contracts are documented in `README.md` with request/response examples.

## Common Tasks

### Adding a Frontend Feature

1. **Create component** in `src/components/`:
   ```tsx
   // src/components/MyComponent.tsx
   export default function MyComponent() { ... }
   ```

2. **Add page** (if needed) in `src/pages/`:
   ```tsx
   // src/pages/MyPage.tsx
   export default function MyPage() { ... }
   ```

3. **Update routing** in `src/App.tsx`:
   ```tsx
   <Route path="/my-page" element={<MyPage />} />
   ```

4. **Create API hook** (if needed) in `src/hooks/`:
   ```tsx
   // src/hooks/useMyData.ts
   export function useMyData() {
     const backendUrl = import.meta.env.VITE_BACKEND_URL;
     // Use fetch with credentials: 'include' for auth
   }
   ```

5. **Add TypeScript types** in `src/types/`:
   ```tsx
   // src/types/index.ts
   export interface MyData { ... }
   ```

### Adding a Backend Endpoint

1. **Create/update router** in `backend/app/routers/`:
   ```python
   # backend/app/routers/my_router.py
   from fastapi import APIRouter, Depends
   from ..auth import get_current_user

   router = APIRouter()

   @router.get("/api/my-endpoint")
   async def my_endpoint(user=Depends(get_current_user)):
       return {"data": "..."}
   ```

2. **Define Pydantic models** in `backend/app/models.py`:
   ```python
   class MyRequest(BaseModel):
       field: str

   class MyResponse(BaseModel):
       data: str
   ```

3. **Include router** in `backend/main.py`:
   ```python
   from app.routers import my_router
   app.include_router(my_router.router)
   ```

4. **Add tests** in `backend/tests/`:
   ```python
   def test_my_endpoint(client, authenticated_user):
       response = client.get("/api/my-endpoint")
       assert response.status_code == 200
   ```

See `backend/CLAUDE.md` for detailed backend development guidelines.

### Connecting Frontend to New Backend Endpoint

1. **Create custom hook** in `src/hooks/`:
   ```tsx
   export function useMyEndpoint() {
     const backendUrl = import.meta.env.VITE_BACKEND_URL;

     const fetchData = async () => {
       const response = await fetch(`${backendUrl}/api/my-endpoint`, {
         credentials: 'include',  // Important for auth cookies
       });
       if (!response.ok) throw new Error('Failed to fetch');
       return response.json();
     };

     return { fetchData };
   }
   ```

2. **Use in component**:
   ```tsx
   import { useMyEndpoint } from '@/hooks/useMyEndpoint';

   function MyComponent() {
     const { fetchData } = useMyEndpoint();
     // Use fetchData in useEffect or event handler
   }
   ```

3. **Add mock data** (for dev mode) in the hook if needed

## Docker & Deployment

### Full Stack with Docker Compose (Recommended)

The easiest way to run the entire application stack (frontend + backend + database) is using the provided `docker.sh` script:

```bash
# Start production environment (all services)
./docker.sh prod start

# Start development environment (all services with hot-reload)
./docker.sh dev start

# View logs from all services
./docker.sh logs -f

# Rebuild and restart (useful after code changes)
./docker.sh prod rebuild

# Stop all services
./docker.sh stop
```

**What gets started:**
- Frontend (React + Vite) on port 8080
- Backend (FastAPI) on port 8000
- MySQL Database on port 3306

**Environment Configuration:**

1. **Root `.env` file** - Controls Docker Compose and frontend build:
   ```bash
   # Copy and customize
   cp .env.example .env

   # Edit these variables:
   VITE_BACKEND_URL=http://localhost:8000
   VITE_DEV_MODE=false
   MYSQL_ROOT_PASSWORD=secure_password
   MYSQL_DATABASE=server_dashboard
   MYSQL_USER=dashboard_user
   MYSQL_PASSWORD=secure_password
   ```

2. **Backend `.env` file** - Backend-specific configuration:
   ```bash
   cd backend
   cp .env.example .env

   # Edit backend/.env with SAML and other settings
   ```

**Docker Compose Files:**
- `docker-compose.yml` - Production configuration
- `docker-compose.dev.yml` - Development configuration (hot-reload, debug logging)

### Individual Service Deployment

#### Frontend Only

```bash
# Build production image (static build with serve)
docker build \
  --build-arg VITE_BACKEND_URL=https://api.example.com \
  --build-arg VITE_DEV_MODE=false \
  -t server-dashboard-frontend:prod .

# Run container
docker run -d --restart=unless-stopped -p 8080:8080 \
  --name server-dashboard-frontend server-dashboard-frontend:prod
```

**Frontend Docker details:**
- Multi-stage build: Node.js for building, serve for hosting
- Static files served on port 8080
- `VITE_BACKEND_URL` baked into build (not runtime-configurable)
- Non-root user (UID 1001)
- Security headers included

#### Backend Only

```bash
# Build backend image
cd backend
docker build -t server-dashboard-backend:prod .

# Run container
docker run -d --restart=unless-stopped \
  -p 8000:8000 \
  -v ./saml_metadata:/app/saml_metadata:ro \
  -v ./.env:/app/.env:ro \
  --name server-dashboard-backend \
  server-dashboard-backend:prod
```

**Backend Docker details:**
- Python 3.11 base image
- Runs as non-root user (UID 1000)
- Gunicorn + Uvicorn workers for production
- Port 8000 exposed
- Environment variables via `.env` file

See `backend/CLAUDE.md` for detailed backend deployment instructions.

## Documentation Reference

- **Root README.md**: General project info, API contracts, environment setup
- **backend/CLAUDE.md**: Detailed backend implementation guide (auth, middleware, testing, SAML config)
- **This file (CLAUDE.md)**: Monorepo structure, integration points, common tasks

## Project-Specific Conventions

### Frontend

- **Component files**: Use default exports
- **Hooks**: Prefix with `use`, return object with methods/state
- **Types**: Define in `src/types/index.ts`
- **Styling**: Tailwind CSS utility classes
- **Routing**: React Router v7 with `createBrowserRouter`
- **State Management**: React Context for auth, local state for components
- **Login Logo**: Customizable via `VITE_LOGIN_LOGO_PATH` (filename in public/ directory) and `VITE_LOGIN_LOGO_BG_COLOR` (Tailwind class). Defaults to Shield icon with green background. Images auto-crop to circle using `object-cover`. Logo files must be placed in `public/` directory before build.

### Backend

- **Routers**: Organize by domain (build, server, assign, preconfig)
- **Models**: Pydantic for all request/response validation
- **Auth**: Use `Depends(get_current_user)` for protected endpoints
- **Testing**: Pytest with fixtures in `conftest.py`
- **Code Quality**: Black for formatting, Ruff for linting

### Region/Depot Mapping

- **CBG (Cambridge)**: depot = 1
- **DUB (Dublin)**: depot = 2
- **DAL (Dallas)**: depot = 4

## Troubleshooting

### Frontend issues

- **"Cannot connect to backend"**: Check `VITE_BACKEND_URL` in `.env`, ensure backend is running
- **Auth redirects not working**: Verify `VITE_DEV_MODE` setting and backend SAML config
- **Build errors**: Run `npm run typecheck` to catch TypeScript errors

### Backend issues

- **SAML errors**: Check `saml_metadata/idp_metadata.xml` exists and is valid
- **Database connection**: Currently using mock data (no database connected)
- **Session issues**: Sessions stored in-memory (use Redis for production)

### Fullstack issues

- **CORS errors**: Verify `CORS_ORIGINS` in backend `.env` includes frontend URL
- **Cookie not sent**: Ensure frontend uses `credentials: 'include'` in fetch calls
- **401 Unauthorized**: Check session is valid, try logging in again

## Security Notes

- Never commit `.env` files (both root and backend have them)
- HTTP-only cookies prevent XSS attacks on session tokens
- CORS configured to specific origins only
- Rate limiting enabled on backend (60/min sustained, 100 burst)
- Security headers automatically added by middleware
- SAML assertions validated and signatures checked
