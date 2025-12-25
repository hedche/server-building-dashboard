# API Reference

Complete REST API documentation for the Server Building Dashboard backend.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Authentication](authentication.md) | SAML login, session management, user info |
| [Build Endpoints](build-endpoints.md) | Build status and history |
| [Server Endpoints](server-endpoints.md) | Server details and assignment |
| [Preconfig Endpoints](preconfig-endpoints.md) | Preconfig management and push |
| [Logs Endpoints](logs-endpoints.md) | Build log retrieval |
| [Error Reference](error-reference.md) | HTTP status codes and error responses |

## Base URL

| Environment | Base URL |
|-------------|----------|
| Development | `http://localhost:8000` |
| Production | `https://api.your-domain.com` |

All endpoints are prefixed with `/api`.

## Authentication

Most endpoints require authentication via session cookie.

### Session Cookie

After SAML authentication, the backend sets an HTTP-only cookie:

```
Set-Cookie: session_token=<token>; HttpOnly; Secure; SameSite=Lax; Path=/
```

### Including Credentials

All API requests must include credentials:

```javascript
fetch('/api/endpoint', {
  credentials: 'include'
});
```

```bash
curl -b cookies.txt -c cookies.txt https://api.example.com/api/endpoint
```

## Request Format

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Cookie` | Yes* | Session token (auto-sent by browser) |
| `Content-Type` | For POST/PUT | `application/json` |
| `X-Request-ID` | No | Correlation ID for tracing |

*Not required for public endpoints (`/api/config`, `/api/health`)

### Request Body

POST and PUT requests use JSON:

```json
{
  "field": "value"
}
```

## Response Format

### Success Response

```json
{
  "data": "...",
  "field": "value"
}
```

### Error Response

```json
{
  "detail": "Error message explaining what went wrong"
}
```

### Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Correlation ID for request tracing |
| `X-RateLimit-Limit` | Rate limit maximum |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Rate limit reset timestamp |

## Endpoints Overview

### Public Endpoints (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Region configuration |
| GET | `/api/health` | Health check |
| GET | `/api` | API info |
| GET | `/api/saml/login` | Initiate SAML login |
| POST | `/api/auth/callback` | SAML callback |

### Protected Endpoints (Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/me` | Current user info |
| POST | `/api/logout` | End session |
| GET | `/api/build-status` | Current builds |
| GET | `/api/build-history/{region}` | Today's builds |
| GET | `/api/build-history/{region}/{date}` | Historical builds |
| GET | `/api/server-details` | Server info |
| POST | `/api/assign` | Assign server |
| GET | `/api/preconfig/{region}` | Region preconfigs |
| GET | `/api/preconfig/pushed` | Pushed preconfigs |
| POST | `/api/preconfig/{region}/push` | Push preconfigs |
| GET | `/api/build-logs/{hostname}` | Get build log |

## Rate Limiting

| Limit Type | Value |
|------------|-------|
| Sustained | 60 requests/minute |
| Burst | 100 requests/minute |

When rate limited, you'll receive:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703596200
Retry-After: 60

{
  "error": "Rate limit exceeded",
  "detail": "Maximum 100 requests per minute allowed"
}
```

## Testing with cURL

### Get Session Cookie

```bash
# After SAML login, save cookies
curl -c cookies.txt -L http://localhost:8000/api/saml/login
```

### Authenticated Request

```bash
curl -b cookies.txt http://localhost:8000/api/me
```

### POST Request

```bash
curl -b cookies.txt \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"serial_number":"SN001","hostname":"srv-001","dbid":"100001"}' \
  http://localhost:8000/api/assign
```

## OpenAPI Documentation

In development mode, interactive API documentation is available:

| URL | Description |
|-----|-------------|
| `/api/docs` | Swagger UI |
| `/api/redoc` | ReDoc |

**Note:** Disabled in production for security.

## Next Steps

- [Authentication](authentication.md) - Login and session management
- [Build Endpoints](build-endpoints.md) - Build status API
- [Error Reference](error-reference.md) - Error handling
