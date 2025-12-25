# Debugging Guide

Techniques for debugging the Server Building Dashboard.

## Debug Logging

### Enable Debug Mode

```env
# backend/.env
LOG_LEVEL=DEBUG
```

Restart backend to apply:
```bash
docker compose restart backend
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql

# Last N lines
docker compose logs --tail=100 backend
```

### Log Output Format

```
Endpoint=/api/build-status Method=GET Status=200 Duration=45ms ClientIP=192.168.1.100 CorrelationID=abc123-def456
```

## Correlation IDs

Every request has a correlation ID for tracing:

### Finding Correlation ID

```bash
# In response headers
curl -v http://localhost:8000/api/me 2>&1 | grep X-Request-ID

# In logs
docker compose logs backend | grep "abc123"
```

### Using Correlation ID

When reporting issues, include the correlation ID to help trace the request through the system.

## Frontend Debugging

### Browser Developer Tools

1. **Console:** View JavaScript errors
2. **Network:** Inspect API requests/responses
3. **Application:** Check cookies, localStorage

### Common Checks

```javascript
// Check if authenticated
document.cookie.includes('session_token')

// Check backend URL
import.meta.env.VITE_BACKEND_URL

// Check dev mode
import.meta.env.VITE_DEV_MODE
```

### React Developer Tools

Install browser extension:
- [Chrome](https://chrome.google.com/webstore/detail/react-developer-tools)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

Inspect:
- Component hierarchy
- Props and state
- Context values

## Backend Debugging

### Interactive Debugging

```bash
# Enter container
docker exec -it server-dashboard-backend bash

# Python shell
python

>>> from app.config import settings
>>> print(settings.DATABASE_URL)
```

### Print Debugging

```python
# Add to code temporarily
print(f"DEBUG: value = {value}")

# Or use logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Processing: {data}")
```

### Request/Response Inspection

```python
@router.get("/debug-endpoint")
async def debug_endpoint(request: Request):
    # Log request details
    print(f"Headers: {dict(request.headers)}")
    print(f"Cookies: {request.cookies}")
    print(f"Query: {dict(request.query_params)}")

    return {"status": "debug"}
```

## Database Debugging

### Connect to MySQL

```bash
# Via Docker
docker exec -it server-dashboard-mysql mysql -u root -p

# SQL commands
SHOW DATABASES;
USE server_dashboard;
SHOW TABLES;
SELECT * FROM sessions LIMIT 5;
```

### Check Query Performance

```sql
-- Enable query log
SET GLOBAL general_log = 'ON';

-- View slow queries
SHOW VARIABLES LIKE 'slow_query%';

-- Check active connections
SHOW PROCESSLIST;
```

## Network Debugging

### Test Connectivity

```bash
# Backend health
curl -v http://localhost:8000/api/health

# With cookies
curl -b cookies.txt http://localhost:8000/api/me

# Check CORS headers
curl -v -X OPTIONS \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  http://localhost:8000/api/build-status
```

### DNS Resolution

```bash
# Inside container
docker exec server-dashboard-backend nslookup mysql
docker exec server-dashboard-backend nslookup cbg-build-01.internal.example.com
```

### Port Connectivity

```bash
# Check ports
netstat -tlnp | grep -E '8000|8080|3306'

# Test connection
nc -zv localhost 8000
```

## SAML Debugging

### Enable SAML Debug

```env
# backend/.env
LOG_LEVEL=DEBUG
```

### Common SAML Issues

```bash
# Check metadata file
cat backend/saml_metadata/idp_metadata.xml | head -20

# Verify EntityID
grep -i entityid backend/saml_metadata/idp_metadata.xml

# Check certificates
grep -i x509certificate backend/saml_metadata/idp_metadata.xml
```

### Decode SAML Response

```python
# Decode base64 SAML response
import base64
response = "PHNhbWxwOl..."  # Base64 SAML response
decoded = base64.b64decode(response).decode('utf-8')
print(decoded)
```

## Docker Debugging

### Container Status

```bash
# List containers
docker ps -a

# Container details
docker inspect server-dashboard-backend

# Resource usage
docker stats
```

### Container Shell

```bash
# Enter running container
docker exec -it server-dashboard-backend bash

# Check processes
ps aux

# Check environment
env | grep -E 'SAML|DB|SECRET'

# Check filesystem
ls -la /app
```

### Image Debugging

```bash
# Build with debug output
docker build --progress=plain -t debug-backend ./backend

# Run with shell
docker run -it --entrypoint /bin/bash server-dashboard-backend
```

## Performance Debugging

### Backend Profiling

```python
import time

@router.get("/slow-endpoint")
async def slow_endpoint():
    start = time.time()

    # ... operation ...
    step1_time = time.time()
    print(f"Step 1: {step1_time - start:.2f}s")

    # ... more operations ...
    step2_time = time.time()
    print(f"Step 2: {step2_time - step1_time:.2f}s")

    return {"total_time": time.time() - start}
```

### Database Query Timing

```python
import time
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, *args):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, *args):
    total = time.time() - conn.info["query_start_time"].pop()
    print(f"Query: {statement[:50]}... Time: {total:.4f}s")
```

### Memory Profiling

```python
import tracemalloc

tracemalloc.start()

# ... code to profile ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

## Test Environment

### Create Test Environment

```bash
# Isolated test network
docker network create test-network

# Run with test config
docker run --rm \
  --network test-network \
  -e ENVIRONMENT=test \
  -e LOG_LEVEL=DEBUG \
  server-dashboard-backend \
  pytest -v tests/
```

### Mock External Services

```python
# tests/conftest.py
from unittest.mock import patch

@pytest.fixture
def mock_build_server():
    with patch('app.routers.preconfig.push_to_server') as mock:
        mock.return_value = {"status": "success"}
        yield mock
```

## Useful Commands Reference

| Task | Command |
|------|---------|
| View all logs | `docker compose logs -f` |
| Backend logs only | `docker compose logs -f backend` |
| Enter container | `docker exec -it server-dashboard-backend bash` |
| MySQL shell | `docker exec -it server-dashboard-mysql mysql -u root -p` |
| Check health | `curl http://localhost:8000/api/health` |
| Test auth | `curl -b cookies.txt http://localhost:8000/api/me` |
| Check ports | `lsof -i :8000` |
| Container stats | `docker stats` |

## Getting More Help

If debugging doesn't resolve the issue:

1. Collect relevant logs
2. Note the correlation ID
3. Document reproduction steps
4. Open an issue with full details

See [Common Issues](common-issues.md) for known problems and solutions.
