# Troubleshooting

Help and support resources for the Server Building Dashboard.

## Quick Navigation

| Guide | Description |
|-------|-------------|
| [Common Issues](common-issues.md) | FAQ and solutions |
| [Debugging](debugging.md) | Debug techniques |

## Getting Help

### 1. Check Documentation

- [Getting Started](../getting-started/README.md) - Setup guides
- [API Reference](../api/README.md) - API documentation
- [Configuration](../getting-started/configuration.md) - Environment variables

### 2. Search Common Issues

See [Common Issues](common-issues.md) for frequently asked questions.

### 3. Enable Debug Logging

```env
# backend/.env
LOG_LEVEL=DEBUG
```

See [Debugging](debugging.md) for techniques.

### 4. Contact Support

- Open an issue on GitHub/GitLab
- Include error messages, logs, and steps to reproduce

## Quick Fixes

### Application Won't Start

```bash
# Check Docker is running
docker info

# Check port availability
lsof -i :8080
lsof -i :8000

# View logs
./docker.sh logs -f
```

### Authentication Issues

```bash
# Verify SAML metadata exists
ls backend/saml_metadata/idp_metadata.xml

# Check SAML configuration
cat backend/.env | grep SAML
```

### Database Issues

```bash
# Check MySQL is running
docker compose ps mysql

# Test connection
docker exec -it server-dashboard-mysql mysql -u root -p
```

### Permission Denied

```bash
# Check user in permissions
cat backend/config/config.json | grep "your-email"
```

## Error Reference

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| 401 Unauthorized | Session expired | Re-login |
| 403 Forbidden | No permission | Check config.json |
| 404 Not Found | Resource missing | Verify resource exists |
| 429 Too Many Requests | Rate limited | Wait and retry |
| 500 Server Error | Backend error | Check logs |

## Health Checks

### Backend Health

```bash
curl http://localhost:8000/api/health

# Expected
{"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### Frontend Health

```bash
curl http://localhost:8080

# Expected: HTML content
```

### Database Health

```bash
docker exec server-dashboard-mysql mysqladmin ping -h localhost
```

## Log Locations

| Service | Location |
|---------|----------|
| Frontend | Docker logs (`docker compose logs frontend`) |
| Backend | Docker logs + `/var/log/server-building-dashboard` |
| MySQL | Docker logs (`docker compose logs mysql`) |
| Nginx | `/var/log/nginx/` |

## Support Information

When reporting issues, include:

1. **Environment**
   - OS and version
   - Docker version
   - Browser (for frontend issues)

2. **Configuration**
   - Relevant .env settings (redact secrets)
   - config.json permissions section

3. **Reproduction Steps**
   - Step-by-step instructions
   - Expected vs actual behavior

4. **Logs**
   - Error messages
   - Correlation IDs
   - Stack traces

## Next Steps

- [Common Issues](common-issues.md) - FAQ
- [Debugging](debugging.md) - Debug techniques
