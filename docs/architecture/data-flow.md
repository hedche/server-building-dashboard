# Data Flow

This document describes the request flows and data patterns in the Server Building Dashboard.

## Authentication Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant F as Frontend
    participant B as Backend
    participant I as SAML IDP

    Note over U,I: Login Flow
    U->>F: Click "Login with SAML"
    F->>B: GET /api/saml/login
    B->>B: Generate SAML Request
    B-->>U: 302 Redirect to IDP

    U->>I: SAML AuthnRequest
    I->>U: Login Form
    U->>I: Enter Credentials
    I->>I: Authenticate User
    I-->>U: SAML Response (POST)

    U->>B: POST /api/auth/callback
    B->>B: Validate SAML Signature
    B->>B: Extract User Attributes
    B->>B: Check Permissions
    B->>B: Create Session
    B-->>U: 302 + Set-Cookie (session_token)

    U->>F: /auth/callback
    F->>B: GET /api/me (with cookie)
    B->>B: Validate Session
    B-->>F: User Data
    F->>F: Update AuthContext
    F-->>U: Redirect to /dashboard

    Note over U,I: Logout Flow
    U->>F: Click Logout
    F->>B: POST /api/logout
    B->>B: Delete Session
    B-->>F: Clear Cookie
    F-->>U: Redirect to /login
```

## API Request Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant F as Frontend
    participant B as Backend
    participant DB as Database

    U->>F: User Action
    F->>F: Call Custom Hook

    Note over F,B: Request with Auth
    F->>B: GET /api/endpoint
    Note right of F: credentials: 'include'<br/>Cookie: session_token=...

    B->>B: Middleware Stack
    Note right of B: 1. Log Request<br/>2. Check Rate Limit<br/>3. Security Headers

    B->>B: get_current_user()
    Note right of B: Validate session_token<br/>Load user permissions

    alt Invalid Session
        B-->>F: 401 Unauthorized
        F-->>U: Redirect to Login
    else Valid Session
        B->>B: Check Region Access
        alt No Access
            B-->>F: 403 Forbidden
        else Has Access
            B->>DB: Query Data
            DB-->>B: Results
            B-->>F: JSON Response
            F->>F: Update State
            F-->>U: Render UI
        end
    end
```

## Build Status Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend
    participant DB as Database

    F->>B: GET /api/build-status
    B->>B: Authenticate User
    B->>DB: SELECT * FROM builds WHERE status='installing'
    DB-->>B: Build Records
    B->>B: Filter by User Regions
    B->>B: Group by Region
    B-->>F: { "cbg": [...], "dub": [...] }

    F->>F: useBuildStatus() updates state
    F->>F: RackVisualization renders

    Note over F: User clicks server
    F->>B: GET /api/server-details?hostname=srv-001
    B->>DB: SELECT * FROM servers WHERE hostname=...
    DB-->>B: Server Record
    B-->>F: ServerDetails JSON
    F->>F: ServerModal displays
```

## Preconfig Push Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    participant BS1 as Build Server 1
    participant BS2 as Build Server 2

    F->>B: POST /api/preconfig/cbg/push
    B->>B: Authenticate & Authorize

    B->>DB: SELECT preconfigs WHERE depot=1 AND created_today
    DB-->>B: Preconfig List

    B->>B: Load Build Server Config
    Note right of B: cbg-build-01: ["small", "medium"]<br/>cbg-build-02: ["large"]

    par Push to Build Servers
        B->>BS1: PUT /preconfig (filtered by size)
        BS1-->>B: 200 OK
    and
        B->>BS2: PUT /preconfig (filtered by size)
        BS2-->>B: 200 OK
    end

    B->>DB: UPDATE preconfigs SET pushed_to=..., last_pushed_at=NOW()
    DB-->>B: Updated

    B-->>F: PushPreconfigResponse
    Note right of B: status: "success"<br/>results: [{server, status}, ...]

    F->>F: Update UI with results
```

## Server Assignment Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend
    participant DB as Database

    Note over F: User selects servers to assign
    F->>F: Check boxes on unassigned servers

    F->>B: POST /api/assign
    Note right of F: { serial_number, hostname, dbid }

    B->>B: Authenticate User
    B->>DB: SELECT * FROM servers WHERE dbid=...
    DB-->>B: Server Record

    B->>B: Check Region Permission
    alt No Access
        B-->>F: 403 Forbidden
    else Has Access
        B->>B: Process Assignment (2s delay)
        B->>DB: UPDATE servers SET assigned_status='assigned',<br/>assigned_by=user.email, assigned_at=NOW()
        DB-->>B: Updated
        B-->>F: { status: "success", message: "..." }
    end

    F->>F: Update assignmentStates
    F->>F: Refetch build history
```

## Build Log Retrieval Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend
    participant FS as File System

    F->>F: User types hostname
    F->>F: Debounce (300ms)
    F->>F: Filter hostnames locally

    Note over F: User selects hostname
    F->>B: GET /api/build-logs/srv-001

    B->>B: Validate hostname format
    Note right of B: HOSTNAME_PATTERN regex

    B->>FS: Search build_logs/*/srv-001/srv-001-Installer.log

    alt Log Found
        B->>B: Validate path (prevent traversal)
        B->>B: Check file size (< 10MB)
        B->>FS: Read file content
        FS-->>B: Log text
        B-->>F: Plain text response
        Note right of B: Content-Type: text/plain<br/>X-Build-Server: cbg-build-01
        F->>F: Display in log viewer
        F->>F: Auto-scroll to bottom
    else Log Not Found
        B-->>F: 404 Not Found
        F->>F: Show error message
    end
```

## Dev Mode Fallback Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant B as Backend

    Note over F,B: VITE_DEV_MODE=true

    F->>F: useBuildStatus() called
    F->>B: GET /api/build-status

    alt Backend Available
        B-->>F: Real Data
        F->>F: Use real data
    else Backend Unavailable (timeout 3s)
        F->>F: Use mock data
        Note right of F: Console: "Backend unavailable,<br/>using mock data"
    end

    Note over F,B: Login in Dev Mode
    F->>F: Click "Dev Mode" toggle
    F->>F: Set mock user in AuthContext
    Note right of F: user: { email: "dev@example.com" }
    F->>F: Navigate to /dashboard
```

## Region Filtering Flow

```mermaid
flowchart TD
    A[API Request] --> B{Is Admin?}
    B -->|Yes| C[Return All Regions]
    B -->|No| D[Get allowed_regions]
    D --> E{Check Each Region}
    E --> F[Filter Results]
    F --> G[Return Filtered Data]

    subgraph "Permission Check"
        H[Load config.json] --> I[Check admins list]
        I --> J[Check builders per region]
        J --> K[Build allowed_regions]
    end
```

## Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NoSession: App Load

    NoSession --> Authenticating: SAML Login
    Authenticating --> Active: Callback Success
    Authenticating --> NoSession: Auth Failed

    Active --> Active: API Request
    Active --> NoSession: Logout
    Active --> Expired: Session Timeout (8h)

    Expired --> NoSession: Next Request

    state Active {
        [*] --> Valid
        Valid --> Valid: Refresh Check
    }
```

## Data Model Relationships

```mermaid
erDiagram
    USER ||--o{ SESSION : has
    USER }|--o{ REGION : "can access"

    REGION ||--o{ BUILD_SERVER : contains
    REGION ||--o{ RACK : contains
    REGION ||--o{ SERVER : hosts

    BUILD_SERVER ||--o{ PRECONFIG : "receives"

    SERVER }|--|| RACK : "located in"
    SERVER }o--o| PRECONFIG : "configured by"

    USER ||--o{ ASSIGNMENT : performs
    ASSIGNMENT }|--|| SERVER : targets
```

## Error Handling Flow

```mermaid
flowchart TD
    A[API Request] --> B{Authenticated?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D{Authorized?}
    D -->|No| E[403 Forbidden]
    D -->|Yes| F{Valid Input?}
    F -->|No| G[400 Bad Request]
    F -->|Yes| H{Rate Limited?}
    H -->|Yes| I[429 Too Many Requests]
    H -->|No| J{Process Request}
    J -->|Error| K[500 Internal Error]
    J -->|Success| L[200 OK]

    C --> M[Frontend: Redirect to Login]
    E --> N[Frontend: Show Error]
    G --> N
    I --> N
    K --> N
    L --> O[Frontend: Update UI]
```

## Next Steps

- [API Reference](../api/README.md) - Detailed endpoint documentation
- [Frontend Architecture](frontend.md) - Component implementation
- [Backend Architecture](backend.md) - Server implementation
