# Frontend Architecture

The frontend is a React 18 application built with TypeScript, Vite, and Tailwind CSS.

## Directory Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx       # Main app shell (sidebar + content)
│   ├── Sidebar.tsx      # Navigation sidebar
│   ├── TopBar.tsx       # Header with user info
│   ├── Logo.tsx         # Customizable logo component
│   ├── ProtectedRoute.tsx  # Auth guard
│   ├── RackVisualization.tsx  # Server rack display
│   ├── ServerModal.tsx  # Server details modal
│   ├── PreconfigModal.tsx  # Preconfig details modal
│   └── HostnameSearch.tsx  # Autocomplete search
├── pages/               # Page components
│   ├── LoginPage.tsx    # SAML login entry
│   ├── AuthCallbackPage.tsx  # SAML callback handler
│   ├── BuildOverviewPage.tsx  # Real-time build status
│   ├── PreconfigPage.tsx  # Preconfig management
│   ├── AssignPage.tsx   # Server assignment
│   ├── BuildLogsPage.tsx  # Log viewer
│   └── CredentialsPage.tsx  # (Placeholder)
├── hooks/               # Custom React hooks
│   ├── useBuildStatus.ts  # Current builds
│   ├── useBuildHistory.ts  # Historical builds
│   ├── useBuildLog.ts   # Build log content
│   ├── useServerDetails.ts  # Server info
│   ├── useHostnames.ts  # Hostname list
│   ├── usePreconfigs.ts  # Preconfig list
│   ├── usePushPreconfig.ts  # Push operation
│   ├── usePushedPreconfigs.ts  # Pushed list
│   ├── useRegionsConfig.ts  # Region configuration
│   └── useAssignServers.ts  # Assignment operation
├── contexts/            # React contexts
│   └── AuthContext.tsx  # Authentication state
├── types/               # TypeScript definitions
│   ├── auth.ts          # User, AuthState
│   └── build.ts         # Server, BuildStatus
├── utils/               # Utilities
│   └── api.ts           # Fetch helpers, dev mode
├── App.tsx              # Router configuration
└── main.tsx             # Application entry
```

## Routing

```mermaid
graph LR
    subgraph "Public Routes"
        LOGIN[/login]
        CALLBACK[/auth/callback]
    end

    subgraph "Protected Routes"
        DASH[/dashboard]
        PRE[/preconfig]
        ASSIGN[/assign]
        LOGS[/build-logs]
        CRED[/credentials]
    end

    ROOT[/] --> DASH
    WILD[/*] --> DASH
```

**Route Configuration (App.tsx):**

| Path | Component | Auth Required |
|------|-----------|---------------|
| `/login` | LoginPage | No |
| `/auth/callback` | AuthCallbackPage | No |
| `/dashboard` | BuildOverviewPage | Yes |
| `/preconfig` | PreconfigPage | Yes |
| `/assign` | AssignPage | Yes |
| `/build-logs` | BuildLogsPage | Yes |
| `/credentials` | CredentialsPage | Yes |

## Component Hierarchy

```
App
├── LoginPage
├── AuthCallbackPage
└── Layout (protected)
    ├── Sidebar
    ├── TopBar
    └── Outlet
        ├── BuildOverviewPage
        │   ├── RackVisualization
        │   └── ServerModal
        ├── PreconfigPage
        │   └── PreconfigModal
        ├── AssignPage
        ├── BuildLogsPage
        │   └── HostnameSearch
        └── CredentialsPage
```

## State Management

### Authentication State (AuthContext)

```typescript
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: () => void;      // Redirect to SAML
  logout: () => void;     // Clear session
  checkAuth: () => void;  // Verify session
}
```

**Usage:**
```tsx
const { user, isAuthenticated, logout } = useAuth();
```

### Server State (Custom Hooks)

Each API endpoint has a dedicated hook managing:
- Data state
- Loading state
- Error state
- Refetch method

**Pattern:**
```typescript
function useBuildStatus() {
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    // Fetch logic with dev mode fallback
  }, []);

  useEffect(() => { refetch(); }, [refetch]);

  return { buildStatus, isLoading, error, refetch };
}
```

### Local State

Component-level state for:
- Modal visibility
- Form inputs
- Selection state
- Sort/filter options

## Custom Hooks Reference

| Hook | API Endpoint | Returns |
|------|--------------|---------|
| `useBuildStatus` | `GET /api/build-status` | Current builds by region |
| `useBuildHistory` | `GET /api/build-history/{region}/{date}` | Historical builds |
| `useBuildLog` | `GET /api/build-logs/{hostname}` | Raw log text |
| `useServerDetails` | `GET /api/server-details?hostname=` | Server details |
| `useHostnames` | `GET /api/hostnames` | All hostnames |
| `usePreconfigs` | `GET /api/preconfig/{region}` | Region preconfigs |
| `usePushPreconfig` | `POST /api/preconfig/{region}/push` | Push operation |
| `usePushedPreconfigs` | `GET /api/preconfig/pushed` | Pushed preconfigs |
| `useRegionsConfig` | `GET /api/config` | Region configuration |
| `useAssignServers` | `POST /api/assign` | Assign operation |

## API Communication

### Fetch Pattern

```typescript
// utils/api.ts
export async function fetchWithFallback<T>(
  endpoint: string,
  options: RequestInit,
  mockData: T
): Promise<T> {
  const backendUrl = getBackendUrl();

  // In dev mode, try backend first, fall back to mock
  if (isDevMode()) {
    try {
      const response = await fetch(`${backendUrl}${endpoint}`, {
        ...options,
        credentials: 'include',
      });
      if (response.ok) return response.json();
    } catch {
      return mockData;
    }
  }

  // In production, always use real backend
  const response = await fetch(`${backendUrl}${endpoint}`, {
    ...options,
    credentials: 'include',
  });
  return response.json();
}
```

### Key Patterns

1. **Always include credentials:**
   ```typescript
   credentials: 'include'  // Sends session cookie
   ```

2. **Dev mode fallback:**
   ```typescript
   if (isDevMode() && !backendAvailable) {
     return mockData;
   }
   ```

3. **Error handling:**
   ```typescript
   if (!response.ok) {
     throw new Error(`API Error: ${response.status}`);
   }
   ```

## Component Patterns

### Protected Route

```tsx
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" />;

  return children;
}
```

### Modal Pattern

```tsx
function ServerModal({ server, onClose }: Props) {
  // Click outside to close
  const handleBackdropClick = (e: MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50" onClick={handleBackdropClick}>
      <div className="modal-content">
        {/* Modal body */}
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
```

### Data Fetching Pattern

```tsx
function BuildOverviewPage() {
  const { buildStatus, isLoading, error, refetch } = useBuildStatus();
  const [selectedRegion, setSelectedRegion] = useState<string>('cbg');

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  const servers = buildStatus?.[selectedRegion] ?? [];

  return (
    <div>
      <RegionSelector value={selectedRegion} onChange={setSelectedRegion} />
      <RackVisualization servers={servers} />
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}
```

## Styling

### Tailwind CSS Classes

**Color Scheme:**
- Background: `bg-gray-900`, `bg-gray-800`
- Text: `text-white`, `text-gray-300`
- Primary: `bg-green-600`, `text-green-400`
- Error: `bg-red-600`, `text-red-400`
- Progress: `bg-blue-600`

**Common Patterns:**
```tsx
// Card
<div className="bg-gray-800 rounded-lg p-4 border border-gray-700">

// Button
<button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded">

// Input
<input className="bg-gray-700 border border-gray-600 rounded px-3 py-2">

// Table
<table className="w-full text-left">
  <thead className="bg-gray-700">
```

### Responsive Design

```tsx
// Grid adapts to screen size
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
```

## Type Definitions

### Core Types

```typescript
// types/auth.ts
interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
}

// types/build.ts
interface Server {
  rackID: string;
  hostname: string;
  dbid: string;
  serial_number: string;
  percent_built: number;
  assigned_status: string;
  machine_type: string;
  status: string;
}

type BuildStatus = Record<string, Server[]>;

interface ServerDetails extends Server {
  ip_address?: string;
  mac_address?: string;
  cpu_model?: string;
  ram_gb?: number;
  storage_gb?: number;
  install_start_time?: string;
  estimated_completion?: string;
  last_heartbeat?: string;
}
```

## Dev Mode

When `VITE_DEV_MODE=true`:

1. **Login bypass**: Click "Dev Mode" button on login page
2. **Mock data**: All hooks return mock data if backend unavailable
3. **Visual indicator**: Yellow "Dev Mode" button in corner
4. **Mock user**: `dev@example.com` with full access

## Next Steps

- [Backend Architecture](backend.md) - API implementation
- [Data Flow](data-flow.md) - Request patterns
- [API Reference](../api/README.md) - Endpoint documentation
