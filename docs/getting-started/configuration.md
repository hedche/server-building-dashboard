# Configuration Reference

Complete reference for all environment variables and configuration options.

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | Frontend build variables and Docker Compose settings |
| `backend/.env` | Backend application configuration |
| `backend/config/config.json` | Region, build server, and permission configuration |

---

## Frontend Environment Variables

Located in `.env` at the repository root.

### Application Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_APP_NAME` | No | "Server Dashboard" | Application name displayed in UI |
| `VITE_BACKEND_URL` | Yes | `http://localhost:8000` | Backend API base URL |
| `VITE_DEV_MODE` | No | `false` | Enable development mode with mock data |

### Branding

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_LOGIN_LOGO_PATH` | No | (Shield icon) | Logo filename in `public/` directory |
| `VITE_LOGIN_LOGO_BG_COLOR` | No | `bg-green-600` | Tailwind CSS background color class |

**Logo Configuration Example:**
```env
# Custom logo
VITE_LOGIN_LOGO_PATH=company-logo.png
VITE_LOGIN_LOGO_BG_COLOR=bg-blue-600
```

Place logo files in the `public/` directory. They're cropped to a circle automatically.

### Docker Compose Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FRONTEND_PORT` | No | `8080` | Frontend container port |
| `BACKEND_PORT` | No | `8000` | Backend container port |
| `MYSQL_PORT` | No | `3306` | MySQL container port |
| `MYSQL_ROOT_PASSWORD` | Yes | - | MySQL root password |
| `MYSQL_DATABASE` | Yes | - | Database name |
| `MYSQL_USER` | Yes | - | Database user |
| `MYSQL_PASSWORD` | Yes | - | Database password |

---

## Backend Environment Variables

Located in `backend/.env`.

### Core Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | "Server Building Dashboard" | Application name |
| `ENVIRONMENT` | No | `dev` | Environment: `dev`, `staging`, `prod` |
| `SECRET_KEY` | **Yes** | - | Session encryption key (generate securely) |
| `SESSION_LIFETIME_SECONDS` | No | `28800` | Session timeout (8 hours) |
| `COOKIE_DOMAIN` | No | - | Cookie domain for cross-domain sessions |

**Generate Secret Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### CORS and Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:8080` | Comma-separated allowed origins |
| `FRONTEND_URL` | Yes | `http://localhost:5173` | Frontend URL for redirects after auth |

### SAML2 Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SAML_METADATA_PATH` | Yes | `./saml_metadata/idp_metadata.xml` | Path to IDP metadata XML |
| `SAML_ACS_URL` | **Yes** | - | Assertion Consumer Service URL |

**SAML Configuration Example:**
```env
SAML_METADATA_PATH=./saml_metadata/idp_metadata.xml
SAML_ACS_URL=https://api.example.com/api/auth/callback
```

The Entity ID is automatically derived from `SAML_ACS_URL` (scheme + host + port).

### Rate Limiting

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | No | `60` | Sustained requests per minute |
| `RATE_LIMIT_BURST` | No | `100` | Maximum burst requests |

### Logging

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_DIR` | No | `/var/log/server-building-dashboard` | Log directory path |

### Build Logs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BUILD_LOGS_DIR` | No | `./build_logs` | Directory containing build log files |
| `HOSTNAME_PATTERN` | No | `^[a-zA-Z0-9._-]+$` | Regex for hostname validation |

**Build Logs Directory Structure:**
```
build_logs/
├── cbg-build-01/
│   └── server-001/
│       └── server-001-Installer.log
├── cbg-build-02/
│   └── ...
└── dub-build-01/
    └── ...
```

### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | - | MySQL connection string |
| `DB_POOL_SIZE` | No | `10` | Connection pool size |
| `DB_MAX_OVERFLOW` | No | `20` | Maximum overflow connections |
| `DB_POOL_RECYCLE` | No | `3600` | Connection recycle time (seconds) |
| `DB_POOL_TIMEOUT` | No | `30` | Connection acquisition timeout |

**Database URL Format:**
```env
DATABASE_URL=mysql+aiomysql://user:password@host:3306/database
```

Leave empty for mock data mode.

### External APIs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PRECONFIG_API_ENDPOINT` | No | - | External preconfig API URL |
| `PRECONFIG_API_PSK` | No | - | Preconfig API pre-shared key |
| `BUILD_SERVER_DOMAIN` | No | - | Domain suffix for build servers |
| `BUILD_SERVER_TIMEOUT` | No | `30` | Request timeout in seconds |

**Build Server Push Configuration:**
```env
BUILD_SERVER_DOMAIN=.internal.example.com
BUILD_SERVER_TIMEOUT=30
```

When pushing preconfigs, the system calls:
`https://{build_server}{BUILD_SERVER_DOMAIN}/preconfig`

---

## Configuration File (config.json)

Located at `backend/config/config.json`.

### Structure

```json
{
  "regions": {
    "cbg": {
      "depot_id": 1,
      "name": "Cambridge",
      "build_servers": {
        "cbg-build-01": {
          "location": "Cambridge DC1",
          "build_racks": [
            {"rack_id": "1-E", "capacity": 10}
          ],
          "preconfigs": ["small", "medium"]
        }
      },
      "racks": {
        "normal": ["1-A", "1-B", "1-C", "1-D", "1-E"],
        "small": ["S1-A", "S1-B"]
      }
    },
    "dub": {
      "depot_id": 2,
      "name": "Dublin",
      "build_servers": {...}
    },
    "dal": {
      "depot_id": 4,
      "name": "Dallas",
      "build_servers": {...}
    }
  },
  "preconfig": {
    "appliance_sizes": ["small", "medium", "large"]
  },
  "permissions": {
    "admins": [
      "admin@example.com"
    ],
    "builders": {
      "cbg": ["builder1@example.com"],
      "dub": ["builder2@example.com"],
      "dal": ["builder3@example.com"]
    }
  }
}
```

### Regions Configuration

| Field | Description |
|-------|-------------|
| `depot_id` | Numeric depot identifier (used in preconfig API) |
| `name` | Human-readable region name |
| `build_servers` | Map of build server hostnames to their configuration |
| `racks.normal` | Standard rack identifiers |
| `racks.small` | Small/specialty rack identifiers |

### Build Server Configuration

| Field | Description |
|-------|-------------|
| `location` | Physical location description |
| `build_racks` | Array of racks this server manages |
| `preconfigs` | Appliance sizes this server accepts |

### Permissions Configuration

| Field | Description |
|-------|-------------|
| `admins` | Email addresses with full access to all regions |
| `builders` | Region-specific access by email address |

See [Permissions](../security/permissions.md) for detailed permission model.

---

## Example Configurations

### Development Environment

**.env:**
```env
VITE_APP_NAME=Server Dashboard (Dev)
VITE_BACKEND_URL=http://localhost:8000
VITE_DEV_MODE=true
```

**backend/.env:**
```env
ENVIRONMENT=dev
SECRET_KEY=dev-secret-key-not-for-production
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=DEBUG
```

### Production Environment

**.env:**
```env
VITE_APP_NAME=Server Dashboard
VITE_BACKEND_URL=https://api.example.com
VITE_DEV_MODE=false
VITE_LOGIN_LOGO_PATH=company-logo.png

MYSQL_ROOT_PASSWORD=<secure-password>
MYSQL_DATABASE=server_dashboard
MYSQL_USER=dashboard_user
MYSQL_PASSWORD=<secure-password>
```

**backend/.env:**
```env
ENVIRONMENT=prod
SECRET_KEY=<generated-secure-key>
COOKIE_DOMAIN=.example.com

CORS_ORIGINS=https://dashboard.example.com
FRONTEND_URL=https://dashboard.example.com

SAML_ACS_URL=https://api.example.com/api/auth/callback
SAML_METADATA_PATH=./saml_metadata/idp_metadata.xml

DATABASE_URL=mysql+aiomysql://dashboard_user:password@mysql:3306/server_dashboard

LOG_LEVEL=INFO
LOG_DIR=/var/log/server-building-dashboard

BUILD_SERVER_DOMAIN=.internal.example.com
BUILD_SERVER_TIMEOUT=30
```

---

## Next Steps

- [Quick Start](quick-start.md) - Get running quickly
- [Installation](installation.md) - Installation options
- [Security Configuration](../security/authentication.md) - SAML setup
- [Production Deployment](../deployment/production.md) - Production checklist
