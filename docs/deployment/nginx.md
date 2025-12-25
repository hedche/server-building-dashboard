# Nginx Configuration

Nginx reverse proxy setup for production deployment.

## Overview

Nginx provides:
- TLS termination
- Reverse proxy to backend/frontend
- Static asset caching
- Security headers
- Load balancing (optional)

## Prerequisites

- Nginx 1.18+
- TLS certificates (Let's Encrypt or commercial)
- DNS configured for your domain

## Basic Configuration

### nginx.conf

```nginx
# /etc/nginx/nginx.conf

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    multi_accept on;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json
               application/javascript application/xml;

    # Security
    server_tokens off;

    include /etc/nginx/conf.d/*.conf;
}
```

### Site Configuration

```nginx
# /etc/nginx/conf.d/server-dashboard.conf

# Upstream definitions
upstream frontend {
    server 127.0.0.1:8080;
    keepalive 32;
}

upstream backend {
    server 127.0.0.1:8000;
    keepalive 16;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name dashboard.example.com api.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Frontend HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dashboard.example.com;

    # TLS Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern TLS only
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://api.example.com; frame-ancestors 'none';" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend application
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # Block hidden files
    location ~ /\. {
        deny all;
    }
}

# Backend API HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.example.com;

    # TLS Configuration (same as frontend)
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000" always;

    # API endpoints
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check (bypass rate limiting)
    location /api/health {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        access_log off;
    }
}
```

## TLS Certificate Setup

### Let's Encrypt with Certbot

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d dashboard.example.com -d api.example.com

# Auto-renewal (add to crontab)
0 0,12 * * * certbot renew --quiet
```

### Manual Certificate

```bash
# Create directory
mkdir -p /etc/nginx/ssl

# Copy certificates
cp fullchain.pem /etc/nginx/ssl/
cp privkey.pem /etc/nginx/ssl/

# Set permissions
chmod 600 /etc/nginx/ssl/privkey.pem
```

## Single Domain Configuration

If using a single domain for both frontend and API:

```nginx
server {
    listen 443 ssl http2;
    server_name dashboard.example.com;

    # TLS config...

    # Frontend
    location / {
        proxy_pass http://frontend;
        # ...
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        # ...
    }
}
```

Update frontend environment:
```env
VITE_BACKEND_URL=https://dashboard.example.com
```

## Load Balancing

### Multiple Backend Instances

```nginx
upstream backend {
    least_conn;
    server backend1:8000 weight=5;
    server backend2:8000 weight=5;
    server backend3:8000 backup;

    keepalive 32;
}
```

### Health Checks (Nginx Plus)

```nginx
upstream backend {
    zone backend 64k;
    server backend1:8000;
    server backend2:8000;

    health_check interval=10s fails=3 passes=2;
}
```

## Rate Limiting

### Configure Rate Limiting

```nginx
http {
    # Define rate limit zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # ...
}

server {
    # API rate limit
    location /api {
        limit_req zone=api burst=20 nodelay;
        limit_req_status 429;
        # ...
    }

    # Stricter limit for login
    location /api/saml/login {
        limit_req zone=login burst=5 nodelay;
        limit_req_status 429;
        # ...
    }
}
```

## WebSocket Support

If adding real-time features:

```nginx
location /ws {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

## Logging

### Access Log Format

```nginx
log_format detailed '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time uct=$upstream_connect_time '
                    'uht=$upstream_header_time urt=$upstream_response_time';

access_log /var/log/nginx/access.log detailed;
```

### Log Rotation

```bash
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 nginx adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

## Testing Configuration

```bash
# Test syntax
nginx -t

# Reload configuration
nginx -s reload

# View current connections
nginx -s status
```

## Docker Integration

### Nginx in Docker Compose

```yaml
services:
  nginx:
    image: nginx:1.25-alpine
    container_name: server-dashboard-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - frontend
      - backend
    networks:
      - app-network
```

## Troubleshooting

### 502 Bad Gateway

```bash
# Check upstream is running
curl http://localhost:8000/api/health

# Check nginx logs
tail -f /var/log/nginx/error.log
```

### 504 Gateway Timeout

```nginx
# Increase timeouts
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

### SSL Errors

```bash
# Test SSL configuration
openssl s_client -connect dashboard.example.com:443

# Check certificate dates
openssl x509 -in /etc/nginx/ssl/fullchain.pem -noout -dates
```

## Performance Tuning

```nginx
# Worker connections
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

# File descriptor limits
worker_rlimit_nofile 8192;

# Optimize for static content
sendfile on;
tcp_nopush on;
tcp_nodelay on;

# Larger buffers
proxy_buffer_size 128k;
proxy_buffers 4 256k;
proxy_busy_buffers_size 256k;
```

## Next Steps

- [Production Guide](production.md) - Complete production checklist
- [Security: Best Practices](../security/best-practices.md) - Security hardening
- [Troubleshooting](../troubleshooting/common-issues.md) - Common issues
