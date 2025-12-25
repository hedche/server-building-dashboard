# Common Issues

Frequently asked questions and solutions.

## Authentication

### "401 Unauthorized" on every request

**Symptoms:**
- All API requests return 401
- `/api/me` returns 401

**Causes:**
1. Session expired
2. Cookie not being sent
3. Session was cleared

**Solutions:**
```bash
# 1. Re-login
# Navigate to /login and authenticate again

# 2. Check credentials are included in fetch
fetch('/api/endpoint', {
  credentials: 'include'  # Required
});

# 3. Check cookie domain matches
# In backend/.env
COOKIE_DOMAIN=.example.com  # Must match frontend domain
```

---

### "403 Forbidden" after successful SAML login

**Symptoms:**
- SAML login succeeds
- Redirect to application fails with 403

**Causes:**
- User not in permissions list

**Solutions:**
```json
// backend/config/config.json
{
  "permissions": {
    "admins": ["your-email@example.com"],
    // OR
    "builders": {
      "cbg": ["your-email@example.com"]
    }
  }
}
```

---

### SAML login redirects to wrong URL

**Symptoms:**
- After SAML auth, redirects to wrong domain
- "Invalid redirect" error

**Causes:**
- FRONTEND_URL misconfigured
- SAML_ACS_URL mismatch

**Solutions:**
```env
# backend/.env
FRONTEND_URL=https://dashboard.example.com
SAML_ACS_URL=https://api.example.com/api/auth/callback
```

---

### "Invalid SAML response" error

**Symptoms:**
- Login fails at callback
- Error mentions SAML validation

**Causes:**
1. Clock skew between servers
2. Expired IDP certificate
3. Wrong IDP metadata

**Solutions:**
```bash
# 1. Sync system time
sudo ntpdate pool.ntp.org

# 2. Update IDP metadata
curl -o backend/saml_metadata/idp_metadata.xml \
  "https://your-idp/metadata"

# 3. Enable debug logging
LOG_LEVEL=DEBUG
```

## Container Issues

### Containers won't start

**Symptoms:**
- `docker compose up` fails
- Containers restart repeatedly

**Causes:**
1. Port already in use
2. Missing environment files
3. Docker not running

**Solutions:**
```bash
# 1. Check ports
lsof -i :8080
lsof -i :8000
kill <PID>

# 2. Create environment files
cp .env.example .env
cd backend && cp .env.example .env

# 3. Start Docker
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker
```

---

### Backend container keeps restarting

**Symptoms:**
- Backend shows "Restarting"
- Health check failing

**Causes:**
1. Missing SAML metadata
2. Invalid configuration
3. Database connection issues

**Solutions:**
```bash
# Check logs
docker compose logs backend

# Common fixes:
# 1. Create SAML metadata
mkdir -p backend/saml_metadata
touch backend/saml_metadata/idp_metadata.xml

# 2. Verify .env exists
ls backend/.env

# 3. Check MySQL is ready
docker compose logs mysql
```

---

### MySQL connection refused

**Symptoms:**
- Backend logs show "Connection refused"
- Database operations fail

**Causes:**
1. MySQL not ready
2. Wrong credentials
3. Network issue

**Solutions:**
```bash
# 1. Wait for MySQL to be ready
docker compose logs mysql | grep "ready for connections"

# 2. Verify credentials match
cat .env | grep MYSQL
cat backend/.env | grep DATABASE_URL

# 3. Test connection manually
docker exec -it server-dashboard-mysql \
  mysql -u dashboard_user -p
```

## Frontend Issues

### Blank page after login

**Symptoms:**
- Login succeeds but page is blank
- Console shows errors

**Causes:**
1. JavaScript error
2. API connection failure
3. CORS error

**Solutions:**
```bash
# 1. Check browser console for errors

# 2. Verify backend URL
cat .env | grep VITE_BACKEND_URL

# 3. Check CORS settings
cat backend/.env | grep CORS_ORIGINS
# Should include frontend URL
```

---

### "Network Error" on API calls

**Symptoms:**
- API requests fail
- "Failed to fetch" in console

**Causes:**
1. Backend not running
2. CORS misconfigured
3. Wrong backend URL

**Solutions:**
```bash
# 1. Check backend is running
curl http://localhost:8000/api/health

# 2. Verify VITE_BACKEND_URL
cat .env | grep VITE_BACKEND_URL

# 3. Check CORS allows frontend origin
cat backend/.env | grep CORS_ORIGINS
```

---

### Dev mode not working

**Symptoms:**
- Dev Mode button doesn't appear
- Mock data not loading

**Causes:**
- VITE_DEV_MODE not set

**Solutions:**
```env
# .env
VITE_DEV_MODE=true
```

Then rebuild:
```bash
npm run dev  # Local
# OR
./docker.sh dev rebuild  # Docker
```

## API Issues

### Rate limit exceeded (429)

**Symptoms:**
- Requests return 429
- "Too Many Requests" error

**Causes:**
- Too many requests in short time

**Solutions:**
```bash
# Wait and retry (see Retry-After header)

# Or increase limits (backend/.env)
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_BURST=200
```

---

### Build log not found (404)

**Symptoms:**
- Log search returns 404
- "Log not found" message

**Causes:**
1. Server not built yet
2. Log archived
3. Wrong hostname

**Solutions:**
```bash
# 1. Check build logs directory
ls backend/build_logs/

# 2. Search for hostname
find backend/build_logs -name "*hostname*"

# 3. Verify hostname format
# Must match: ^[a-zA-Z0-9._-]+$
```

---

### Preconfig push fails

**Symptoms:**
- Push returns errors
- Build servers unreachable

**Causes:**
1. Build server offline
2. Network/firewall issue
3. Wrong domain suffix

**Solutions:**
```bash
# 1. Check build server connectivity
curl https://cbg-build-01.internal.example.com/health

# 2. Verify domain configuration
cat backend/.env | grep BUILD_SERVER_DOMAIN

# 3. Check config.json build servers
cat backend/config/config.json | grep build_servers
```

## Performance Issues

### Slow page loads

**Symptoms:**
- Pages take long to load
- Spinners shown for extended time

**Causes:**
1. Database queries slow
2. External API latency
3. Large data sets

**Solutions:**
```bash
# 1. Check backend response time
time curl http://localhost:8000/api/build-status

# 2. Enable debug logging to see query times
LOG_LEVEL=DEBUG

# 3. Check database performance
docker exec server-dashboard-mysql \
  mysql -e "SHOW PROCESSLIST"
```

---

### High memory usage

**Symptoms:**
- Containers using excessive memory
- OOM kills

**Causes:**
1. Memory leaks
2. Insufficient limits
3. Large sessions

**Solutions:**
```yaml
# docker-compose.yml - adjust limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

## Configuration Issues

### Changes not taking effect

**Symptoms:**
- Config changes don't apply
- Old values still used

**Causes:**
1. Container using old image
2. Volume caching
3. Environment not reloaded

**Solutions:**
```bash
# Rebuild and restart
./docker.sh prod rebuild

# Or force recreate
docker compose up -d --force-recreate
```

---

### Region not showing

**Symptoms:**
- Region missing from dropdown
- Empty region list

**Causes:**
1. User doesn't have access
2. Region not in config

**Solutions:**
```json
// Check config.json includes region
{
  "regions": {
    "cbg": {...},
    "dub": {...},
    "dal": {...}
  }
}

// Check user has access
{
  "permissions": {
    "builders": {
      "cbg": ["user@example.com"]
    }
  }
}
```

## Still Need Help?

1. Check [Debugging Guide](debugging.md)
2. Search existing issues on GitHub/GitLab
3. Open a new issue with:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Relevant logs
