# Security Best Practices

Security hardening guide for the Server Building Dashboard.

## Secret Management

### Generate Strong Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate database password
openssl rand -base64 24
```

### Never Commit Secrets

```gitignore
# .gitignore
.env
backend/.env
*.pem
*.key
```

### Production Secret Storage

| Method | Use Case |
|--------|----------|
| Docker Secrets | Docker Swarm deployments |
| HashiCorp Vault | Enterprise secret management |
| AWS SSM | AWS deployments |
| Azure Key Vault | Azure deployments |
| Kubernetes Secrets | K8s deployments |

### Example: Docker Secrets

```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - secret_key
      - db_password

secrets:
  secret_key:
    external: true
  db_password:
    external: true
```

```bash
# Create secrets
echo "your-secret-key" | docker secret create secret_key -
```

## TLS Configuration

### Required Settings

```nginx
# Modern TLS only
ssl_protocols TLSv1.2 TLSv1.3;

# Strong ciphers
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

# Prefer server ciphers (TLS 1.2)
ssl_prefer_server_ciphers on;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

### Certificate Management

```bash
# Auto-renewal with Certbot
certbot renew --quiet

# Monitor expiration
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Security Headers

### Required Headers

```nginx
# Prevent MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# Prevent clickjacking
add_header X-Frame-Options "DENY" always;

# XSS protection
add_header X-XSS-Protection "1; mode=block" always;

# Referrer policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions policy
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### Content Security Policy

```nginx
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data:;
  font-src 'self';
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
" always;
```

## Container Security

### Non-Root User

```dockerfile
# Frontend
USER 1001

# Backend
USER 1000
```

### Read-Only Filesystem

```yaml
services:
  backend:
    read_only: true
    tmpfs:
      - /tmp
      - /app/.cache
```

### Drop Capabilities

```yaml
services:
  backend:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
```

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
```

## Network Security

### Internal Networks

```yaml
networks:
  internal:
    driver: bridge
    internal: true  # No external access

  external:
    driver: bridge
```

### Firewall Rules

```bash
# Allow only necessary ports
ufw default deny incoming
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect)
ufw allow 443/tcp   # HTTPS
ufw enable
```

### Database Access

```yaml
services:
  mysql:
    networks:
      - internal  # Only internal access
    # No ports exposed to host
```

## Session Security

### Cookie Configuration

```python
response.set_cookie(
    key="session_token",
    value=token,
    httponly=True,      # No JS access
    secure=True,        # HTTPS only
    samesite="Lax",     # CSRF protection
    max_age=28800,      # 8 hours
    path="/"
)
```

### Session Timeout

```env
# 4 hours for sensitive environments
SESSION_LIFETIME_SECONDS=14400
```

### Session Invalidation

- Logout clears session server-side
- Cookie is deleted client-side
- Session store is cleared

## Input Validation

### Hostname Validation

```python
HOSTNAME_PATTERN = r"^[a-zA-Z0-9._-]+$"

if not re.match(HOSTNAME_PATTERN, hostname):
    raise HTTPException(400, "Invalid hostname")
```

### Path Traversal Prevention

```python
resolved_path = log_path.resolve()
if not resolved_path.is_relative_to(allowed_dir):
    raise HTTPException(400, "Invalid path")
```

### Request Body Validation

```python
class AssignRequest(BaseModel):
    serial_number: str = Field(min_length=1, max_length=100)
    hostname: str = Field(min_length=1, max_length=253)
    dbid: str = Field(min_length=1, max_length=50)

    @validator('hostname')
    def validate_hostname(cls, v):
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Invalid hostname')
        return v
```

## Rate Limiting

### Configuration

```env
RATE_LIMIT_PER_MINUTE=60    # Sustained limit
RATE_LIMIT_BURST=100        # Burst limit
```

### Per-Endpoint Limits

Consider stricter limits for:
- `/api/saml/login` - Login attempts
- `/api/assign` - State-changing operations
- `/api/preconfig/*/push` - External communications

## Logging and Monitoring

### Secure Logging

```python
# DON'T log sensitive data
logger.info(f"User {email} logged in")  # OK
logger.info(f"Password: {password}")    # BAD

# Use correlation IDs
logger.info(f"Request processed", extra={"correlation_id": id})
```

### Monitor for Attacks

- Failed login attempts
- Rate limit hits
- 4xx/5xx error spikes
- Unusual access patterns

### Alerting

Set up alerts for:
- > 10 failed logins per minute
- Any 500 errors
- Service unavailability
- Certificate expiration (< 30 days)

## Dependency Management

### Keep Dependencies Updated

```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt
npm audit fix
```

### Pin Versions

```
# requirements.txt
fastapi==0.109.0
uvicorn==0.25.0
```

### Review Before Updating

- Read changelogs for security fixes
- Test thoroughly before deploying
- Have rollback plan

## SAML Security

### Validate Signatures

```python
# Enable in production
{
    "security": {
        "wantAssertionsSigned": True,
        "wantMessagesSigned": True
    }
}
```

### Limit Token Lifetime

Configure in IDP:
- Short assertion validity (5-10 minutes)
- Short session lifetime

### Attribute Filtering

Only request necessary attributes:
- Email (required)
- Name (optional)
- Groups (for roles)

## Backup Security

### Encrypted Backups

```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup.sql

# Decrypt
gpg --decrypt backup.sql.gpg > backup.sql
```

### Secure Storage

- Offsite storage
- Access controls
- Retention policy
- Regular restore testing

## Incident Response

### Preparation

1. Document procedures
2. Define roles and responsibilities
3. Set up communication channels
4. Practice regularly

### During Incident

1. Contain - Limit damage
2. Investigate - Determine scope
3. Eradicate - Remove threat
4. Recover - Restore service
5. Document - Record actions

### Post-Incident

1. Review what happened
2. Identify improvements
3. Update procedures
4. Implement changes

## Checklist

### Initial Deployment

- [ ] Generate unique SECRET_KEY
- [ ] Configure TLS with valid certificates
- [ ] Enable HSTS
- [ ] Set security headers
- [ ] Restrict CORS origins
- [ ] Configure rate limiting
- [ ] Set up monitoring
- [ ] Review permissions
- [ ] Disable debug endpoints
- [ ] Configure firewall

### Ongoing

- [ ] Update dependencies monthly
- [ ] Review logs weekly
- [ ] Rotate secrets quarterly
- [ ] Conduct security review annually
- [ ] Test backups monthly
- [ ] Practice incident response

## Next Steps

- [Authentication](authentication.md) - SAML configuration
- [Permissions](permissions.md) - Access control
- [Production Deployment](../deployment/production.md) - Deployment guide
