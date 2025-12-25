# Authentication Configuration

Complete guide for setting up SAML2 authentication.

## Overview

The Server Building Dashboard uses SAML 2.0 for enterprise single sign-on (SSO) with support for:
- Microsoft Azure AD
- Active Directory Federation Services (ADFS)
- Okta
- Other SAML 2.0 compliant identity providers

## Prerequisites

- SAML 2.0 compliant identity provider
- IDP administrator access
- Backend server with HTTPS (production)

## Configuration Steps

### 1. Obtain IDP Metadata

Get the metadata XML from your identity provider:

**Azure AD:**
```
https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml
```

**ADFS:**
```
https://{adfs-server}/FederationMetadata/2007-06/FederationMetadata.xml
```

**Okta:**
```
https://{your-domain}.okta.com/app/{app-id}/sso/saml/metadata
```

### 2. Save IDP Metadata

```bash
# Create directory
mkdir -p backend/saml_metadata

# Save metadata
curl -o backend/saml_metadata/idp_metadata.xml \
  "https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml"
```

### 3. Configure Environment

```env
# backend/.env

# SAML Configuration
SAML_METADATA_PATH=./saml_metadata/idp_metadata.xml
SAML_ACS_URL=https://api.example.com/api/auth/callback

# Frontend redirect after auth
FRONTEND_URL=https://dashboard.example.com
```

### 4. Register Application with IDP

#### Azure AD

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Configure:
   - Name: "Server Building Dashboard"
   - Redirect URI: `https://api.example.com/api/auth/callback`
4. Go to "Expose an API" → Set Application ID URI
5. Go to "Token configuration" → Add claims:
   - email
   - given_name
   - family_name
   - groups

#### ADFS

1. Open AD FS Management
2. Add Relying Party Trust
3. Configure claims rules:
   ```
   Send Email as Name ID
   Send givenName as givenname
   Send surname as surname
   Send Group Membership as groups
   ```

## SAML Settings

### Service Provider Configuration

The backend automatically configures these settings:

| Setting | Value |
|---------|-------|
| Entity ID | Derived from `SAML_ACS_URL` origin |
| ACS URL | `{SAML_ACS_URL}` |
| Name ID Format | emailAddress |
| Binding | HTTP-POST |

### Security Settings

```python
# Current security settings (relaxed for compatibility)
{
    "strict": True,
    "security": {
        "nameIdEncrypted": False,
        "authnRequestsSigned": False,
        "logoutRequestSigned": False,
        "wantMessagesSigned": False,
        "wantAssertionsSigned": False,
        "wantAssertionsEncrypted": False,
        "requestedAuthnContext": False
    }
}
```

For stricter security, enable assertion signing in both IDP and application.

## Attribute Mapping

### Expected Attributes

| SAML Attribute | User Field | Fallback |
|----------------|------------|----------|
| NameID | email | - |
| `.../claims/emailaddress` | email | mail, email |
| `.../claims/givenname` | name (first) | givenname, firstname |
| `.../claims/surname` | name (last) | surname, lastname |
| `.../claims/groups` | groups | groups |

### Full Attribute URIs

```
http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname
http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname
http://schemas.microsoft.com/ws/2008/06/identity/claims/groups
```

## Role Mapping

Roles are determined by group membership:

### Default Groups

| Role | Groups |
|------|--------|
| admin | Dashboard-Admins, IT-Admins |
| operator | Dashboard-Operators, IT-Operators |
| user | (default) |

### Customizing Roles

Modify `backend/app/auth.py`:

```python
def _determine_role(self, groups: Any) -> str:
    admin_groups = ["Dashboard-Admins", "IT-Admins", "Your-Admin-Group"]
    operator_groups = ["Dashboard-Operators", "IT-Operators", "Your-Operator-Group"]

    if any(g in admin_groups for g in groups):
        return "admin"
    elif any(g in operator_groups for g in groups):
        return "operator"
    else:
        return "user"
```

## Session Management

### Session Creation

After successful SAML authentication:

1. Validate SAML response signature
2. Extract user attributes
3. Check user has dashboard access (in permissions)
4. Generate session token
5. Store session with expiration
6. Set HTTP-only cookie

### Session Cookie

```python
Set-Cookie: session_token=<token>;
    HttpOnly;
    Secure;
    SameSite=Lax;
    Path=/;
    Max-Age=28800
```

### Session Duration

Default: 8 hours (28800 seconds)

Configure via `SESSION_LIFETIME_SECONDS`:

```env
SESSION_LIFETIME_SECONDS=14400  # 4 hours
```

## Testing Authentication

### Development Mode

Set `VITE_DEV_MODE=true` to bypass SAML:

```bash
# .env
VITE_DEV_MODE=true
```

Click "Dev Mode" on login page to authenticate as:
```javascript
{
  id: 'dev-user',
  email: 'dev@example.com',
  name: 'Dev User',
  role: 'developer'
}
```

### Test SAML Flow

```bash
# 1. Start login flow
curl -v http://localhost:8000/api/saml/login

# 2. Follow redirect to IDP
# 3. Authenticate with IDP
# 4. IDP posts to callback

# 5. Check session
curl -b cookies.txt http://localhost:8000/api/me
```

## Troubleshooting

### SAML Response Errors

**"Invalid SAML response"**
- Check IDP metadata is current
- Verify ACS URL matches exactly
- Check clock sync between servers

**"Signature validation failed"**
- Ensure IDP metadata includes correct certificate
- IDP may have rotated certificates

**"No email in SAML response"**
- Configure IDP to send email claim
- Check attribute mapping configuration

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

This logs:
- SAML request details
- SAML response parsing
- Attribute extraction
- Error details

### Common Issues

| Issue | Solution |
|-------|----------|
| Redirect loop | Check FRONTEND_URL matches actual frontend |
| Cookie not set | Verify HTTPS in production |
| 403 after login | User not in permissions list |
| Clock skew error | Sync NTP on all servers |

## Azure AD Specific

### Required API Permissions

- User.Read (delegated)
- Directory.Read.All (for groups)

### Group Claims

Azure AD has a limit of 200 groups in tokens. For users with many groups:

1. Use application-specific groups
2. Or configure group filtering in Azure AD

### Manifest Configuration

```json
{
  "groupMembershipClaims": "SecurityGroup",
  "optionalClaims": {
    "saml2Token": [
      {
        "name": "groups",
        "essential": true
      }
    ]
  }
}
```

## ADFS Specific

### Claims Rules

```
# Email as Name ID
c:[Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"]
=> issue(Type = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier",
         Value = c.Value);

# Email claim
c:[Type == "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"]
=> issue(claim = c);

# Groups
c:[Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/groupsid"]
=> issue(claim = c);
```

### Token Lifetime

Configure in ADFS:
- Web SSO lifetime
- Token lifetime

## Security Recommendations

1. **Use HTTPS** - Required for Secure cookies
2. **Validate signatures** - Enable assertion signing
3. **Short session lifetimes** - 4-8 hours recommended
4. **Limit groups** - Only send required groups
5. **Monitor logins** - Log and alert on failures

## Next Steps

- [Permissions](permissions.md) - Configure access control
- [Best Practices](best-practices.md) - Security hardening
- [API: Authentication](../api/authentication.md) - API reference
