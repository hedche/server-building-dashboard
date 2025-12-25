# Production Deployment

Complete checklist and guide for production deployment.

## Pre-Deployment Checklist

### Security

- [ ] Generate cryptographically secure `SECRET_KEY`
- [ ] Configure SAML IDP with production URLs
- [ ] Set up TLS certificates
- [ ] Review and restrict CORS origins
- [ ] Disable API docs (`/api/docs`, `/api/redoc`)
- [ ] Configure proper cookie domain
- [ ] Review rate limiting settings
- [ ] Set up firewall rules

### Infrastructure

- [ ] Provision production servers
- [ ] Set up load balancer (if needed)
- [ ] Configure DNS records
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up database backups
- [ ] Plan disaster recovery

### Application

- [ ] Review all environment variables
- [ ] Configure region and permission settings
- [ ] Set up build server connectivity
- [ ] Test SAML authentication flow
- [ ] Verify preconfig API integration
- [ ] Test build log retrieval

## Security Configuration

### Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Never use the default or example key in production!**

### Environment Variables

```env
# backend/.env - Production Settings

# Core
ENVIRONMENT=prod
SECRET_KEY=<generated-secure-key>
SESSION_LIFETIME_SECONDS=28800

# CORS (restrictive)
CORS_ORIGINS=https://dashboard.example.com
COOKIE_DOMAIN=.example.com

# SAML (HTTPS required)
SAML_ACS_URL=https://api.example.com/api/auth/callback
SAML_METADATA_PATH=./saml_metadata/idp_metadata.xml

# Frontend redirect
FRONTEND_URL=https://dashboard.example.com

# Database
DATABASE_URL=mysql+aiomysql://user:password@mysql:3306/server_dashboard

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/server-building-dashboard

# Rate Limiting (adjust as needed)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
```

### TLS Configuration

See [Nginx Guide](nginx.md) for TLS setup with:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS headers
- Certificate management

## Docker Production Setup

### docker-compose.yml Recommendations

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: server-dashboard-mysql
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql-data:/var/lib/mysql
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  backend:
    image: myregistry/dashboard-backend:${VERSION}
    container_name: server-dashboard-backend
    restart: unless-stopped
    depends_on:
      mysql:
        condition: service_healthy
    environment:
      - ENVIRONMENT=prod
    volumes:
      - ./backend/saml_metadata:/app/saml_metadata:ro
      - ./backend/.env:/app/.env:ro
      - /var/log/server-building-dashboard:/var/log/server-building-dashboard
    networks:
      - internal
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/.cache
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: myregistry/dashboard-frontend:${VERSION}
    container_name: server-dashboard-frontend
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

networks:
  internal:
    driver: bridge

volumes:
  mysql-data:
```

## Database Setup

### Initialize Database

```sql
-- Create production database
CREATE DATABASE server_dashboard
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create application user
CREATE USER 'dashboard_user'@'%'
  IDENTIFIED BY 'secure_password_here';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE
  ON server_dashboard.*
  TO 'dashboard_user'@'%';

FLUSH PRIVILEGES;
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily database backup

DATE=$(date +%Y%m%d)
BACKUP_DIR=/var/backups/server-dashboard

# Create backup
docker exec server-dashboard-mysql \
  mysqldump -u root -p${MYSQL_ROOT_PASSWORD} server_dashboard \
  > ${BACKUP_DIR}/backup-${DATE}.sql

# Compress
gzip ${BACKUP_DIR}/backup-${DATE}.sql

# Rotate (keep 30 days)
find ${BACKUP_DIR} -name "backup-*.sql.gz" -mtime +30 -delete
```

Add to cron:
```bash
0 2 * * * /path/to/backup.sh
```

## Monitoring

### Health Check Endpoints

```bash
# Backend health
curl -f https://api.example.com/api/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "version": "1.0.0"
}
```

### Prometheus Metrics (Future)

Consider adding Prometheus metrics for:
- Request latency
- Error rates
- Active sessions
- Database connection pool

### Alerting

Set up alerts for:
- Container restarts
- High error rates (5xx responses)
- Slow response times
- Database connection failures
- Disk space usage
- Memory usage

## Logging

### Structured Logging

Backend logs include correlation IDs:

```
Endpoint=/api/build-status Method=GET Status=200 Duration=45ms CorrelationID=abc123
```

### Log Aggregation

Configure Docker logging driver:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Or use centralized logging:

```yaml
services:
  backend:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://loghost:514"
        tag: "server-dashboard-backend"
```

## Scaling Considerations

### Current Limitations

| Component | Limitation | Solution |
|-----------|------------|----------|
| Sessions | In-memory | Redis |
| Rate limiting | In-memory | Redis |
| Workers | Single | Increase after Redis |

### Adding Redis

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: server-dashboard-redis
    restart: unless-stopped
    networks:
      - internal
    volumes:
      - redis-data:/data
```

Update backend to use Redis for sessions and rate limiting.

### Load Balancing

For multiple instances:

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
}
```

## Security Hardening

### Firewall Rules

```bash
# Allow only necessary ports
ufw default deny incoming
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP (redirect to HTTPS)
ufw allow 443/tcp     # HTTPS
ufw enable
```

### Docker Security

```yaml
# docker-compose.yml security settings
services:
  backend:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
```

### Network Isolation

```yaml
networks:
  internal:
    driver: bridge
    internal: true  # No external access
  external:
    driver: bridge
```

## Deployment Process

### Blue-Green Deployment

1. Deploy new version to "green" environment
2. Run health checks
3. Switch traffic from "blue" to "green"
4. Keep "blue" for rollback

### Rolling Update

```bash
# Pull new images
docker compose pull

# Update services one at a time
docker compose up -d --no-deps backend
docker compose up -d --no-deps frontend
```

### Rollback

```bash
# Quick rollback
docker compose down
docker compose -f docker-compose.backup.yml up -d

# Or revert to previous image
docker compose up -d --force-recreate
```

## Post-Deployment

### Verify Deployment

1. Check container health: `docker ps`
2. Test health endpoint: `curl /api/health`
3. Test login flow
4. Verify SAML integration
5. Test all features

### Documentation

- Update runbook with deployment steps
- Document environment-specific configurations
- Record version deployed and timestamp

## Next Steps

- [Nginx Guide](nginx.md) - Reverse proxy setup
- [Security: Best Practices](../security/best-practices.md) - Security hardening
- [Troubleshooting](../troubleshooting/common-issues.md) - Common issues
