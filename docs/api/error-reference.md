# Error Reference

HTTP status codes and error responses for the Server Building Dashboard API.

## HTTP Status Codes

### Success Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request succeeded |
| 302 | Found | Redirect (SAML flows) |

### Client Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid input, missing parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Access denied to resource |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Server-side error |

---

## Error Response Format

All errors return JSON with a `detail` field:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Rate limit errors include additional fields:

```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 100 requests per minute allowed"
}
```

---

## Error Codes by Endpoint

### Authentication Endpoints

#### GET /api/saml/login

| Status | Cause | Solution |
|--------|-------|----------|
| 500 | SAML configuration error | Check SAML_METADATA_PATH and IDP metadata |

#### POST /api/auth/callback

| Status | Cause | Solution |
|--------|-------|----------|
| 401 | Invalid SAML response | Check IDP configuration |
| 401 | SAML signature validation failed | Verify IDP metadata matches |
| 403 | User not in permission list | Add user to config.json permissions |

#### GET /api/me

| Status | Cause | Solution |
|--------|-------|----------|
| 401 | No session cookie | User needs to login |
| 401 | Session expired | Re-authenticate |
| 401 | Invalid session token | Re-authenticate |

#### POST /api/logout

| Status | Cause | Solution |
|--------|-------|----------|
| 401 | No valid session | N/A (already logged out) |

---

### Build Endpoints

#### GET /api/build-status

| Status | Cause | Solution |
|--------|-------|----------|
| 401 | Not authenticated | Login first |

#### GET /api/build-history/{region}

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid region code | Use cbg, dub, or dal |
| 401 | Not authenticated | Login first |
| 403 | No access to region | Contact admin for access |

#### GET /api/build-history/{region}/{date}

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid region code | Use cbg, dub, or dal |
| 400 | Invalid date format | Use YYYY-MM-DD format |
| 401 | Not authenticated | Login first |
| 403 | No access to region | Contact admin for access |

---

### Server Endpoints

#### GET /api/server-details

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Missing hostname parameter | Include ?hostname=... |
| 401 | Not authenticated | Login first |
| 404 | Server not found | Verify hostname exists |

#### POST /api/assign

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Missing required fields | Include serial_number, hostname, dbid |
| 401 | Not authenticated | Login first |
| 403 | No access to server's region | Contact admin for access |
| 404 | Server not found | Verify dbid exists |

---

### Preconfig Endpoints

#### GET /api/preconfig/{region}

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid region code | Use cbg, dub, or dal |
| 401 | Not authenticated | Login first |
| 403 | No access to region | Contact admin for access |

#### GET /api/preconfig/pushed

| Status | Cause | Solution |
|--------|-------|----------|
| 401 | Not authenticated | Login first |

#### POST /api/preconfig/{region}/push

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid region code | Use cbg, dub, or dal |
| 401 | Not authenticated | Login first |
| 403 | No access to region | Contact admin for access |
| 404 | No build servers configured | Check config.json |

---

### Build Logs Endpoint

#### GET /api/build-logs/{hostname}

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid hostname format | Check hostname pattern |
| 400 | Hostname too long | Max 253 characters |
| 401 | Not authenticated | Login first |
| 404 | Log file not found | Verify hostname has a log |
| 500 | Log file too large | Max 10MB |
| 500 | Permission denied | Check file permissions |
| 500 | Invalid file encoding | Must be UTF-8 |

---

## Common Error Scenarios

### 401 Unauthorized

**Causes:**
- Session cookie missing or expired
- Browser not sending credentials
- Cookie blocked by browser settings

**Frontend Handling:**
```typescript
if (response.status === 401) {
  // Redirect to login
  window.location.href = '/login';
}
```

**cURL Debugging:**
```bash
# Ensure cookies are saved and sent
curl -c cookies.txt -b cookies.txt http://localhost:8000/api/me
```

---

### 403 Forbidden

**Causes:**
- User authenticated but lacks permission
- Region access not granted
- User not in any permission group

**Frontend Handling:**
```typescript
if (response.status === 403) {
  showError('You do not have access to this resource');
}
```

**Resolution:**
Add user to `config.json`:
```json
{
  "permissions": {
    "admins": ["admin@example.com"],
    "builders": {
      "cbg": ["user@example.com"]
    }
  }
}
```

---

### 429 Too Many Requests

**Causes:**
- Exceeded 60 requests/minute (sustained)
- Exceeded 100 requests/minute (burst)

**Response:**
```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 100 requests per minute allowed"
}
```

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703596200
Retry-After: 60
```

**Frontend Handling:**
```typescript
if (response.status === 429) {
  const retryAfter = response.headers.get('Retry-After');
  showError(`Rate limited. Try again in ${retryAfter} seconds.`);
}
```

---

### 500 Internal Server Error

**Causes:**
- Database connection failure
- External API failure
- Unexpected exception

**Response:**
```json
{
  "detail": "Internal server error"
}
```

**Debugging:**
Check backend logs:
```bash
docker compose logs backend -f
```

Look for correlation ID:
```
CorrelationID=abc123... Error: Connection refused
```

---

## Error Handling Best Practices

### Frontend Error Handler

```typescript
async function apiRequest(url: string, options?: RequestInit) {
  const response = await fetch(url, {
    ...options,
    credentials: 'include'
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}`
    }));

    switch (response.status) {
      case 401:
        // Redirect to login
        window.location.href = '/login';
        break;
      case 403:
        throw new Error('Access denied: ' + error.detail);
      case 404:
        throw new Error('Not found: ' + error.detail);
      case 429:
        throw new Error('Rate limited. Please wait and try again.');
      default:
        throw new Error(error.detail || 'An error occurred');
    }
  }

  return response;
}
```

### Retry Logic

```typescript
async function fetchWithRetry(url: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, { credentials: 'include' });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        continue;
      }

      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(r => setTimeout(r, 1000 * (i + 1)));
    }
  }
}
```

---

## Correlation IDs

All requests include a correlation ID for tracing:

**Request Header:**
```http
X-Request-ID: abc123-def456-ghi789
```

**Response Header:**
```http
X-Request-ID: abc123-def456-ghi789
```

**In Logs:**
```
Endpoint=/api/build-status Method=GET Status=200 Duration=45ms CorrelationID=abc123-def456-ghi789
```

Use this ID when reporting issues or debugging.

---

## Next Steps

- [API Overview](README.md) - API documentation index
- [Authentication](authentication.md) - Auth flow details
- [Troubleshooting](../troubleshooting/common-issues.md) - Common issues
