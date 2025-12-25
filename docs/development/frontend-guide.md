# Frontend Development Guide

Guide for React/TypeScript frontend development.

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3 | UI framework |
| TypeScript | 5.5 | Type safety |
| Vite | 5.4 | Build tool |
| Tailwind CSS | 3.4 | Styling |
| React Router | 7.9 | Routing |
| Lucide React | 0.344 | Icons |

## Project Structure

```
src/
├── components/         # Reusable UI components
│   ├── Layout.tsx      # Main app shell
│   ├── Sidebar.tsx     # Navigation
│   ├── TopBar.tsx      # Header
│   └── ...
├── pages/              # Page components
│   ├── BuildOverviewPage.tsx
│   ├── PreconfigPage.tsx
│   └── ...
├── hooks/              # Custom React hooks
│   ├── useBuildStatus.ts
│   ├── useServerDetails.ts
│   └── ...
├── contexts/           # React contexts
│   └── AuthContext.tsx
├── types/              # TypeScript definitions
│   ├── auth.ts
│   └── build.ts
├── utils/              # Utilities
│   └── api.ts
├── App.tsx             # Router configuration
└── main.tsx            # Entry point
```

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type check
npm run typecheck

# Lint
npm run lint
```

## Component Patterns

### Functional Components

```tsx
// src/components/ServerCard.tsx
import { Server } from '@/types/build';

interface ServerCardProps {
  server: Server;
  onClick?: () => void;
}

export default function ServerCard({ server, onClick }: ServerCardProps) {
  return (
    <div
      className="bg-gray-800 rounded-lg p-4 cursor-pointer hover:bg-gray-700"
      onClick={onClick}
    >
      <h3 className="text-white font-medium">{server.hostname}</h3>
      <p className="text-gray-400">{server.percent_built}%</p>
    </div>
  );
}
```

### Page Components

```tsx
// src/pages/ExamplePage.tsx
import { useState, useEffect } from 'react';
import { useExampleData } from '@/hooks/useExampleData';

export default function ExamplePage() {
  const { data, isLoading, error, refetch } = useExampleData();
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  if (isLoading) {
    return <div className="text-white">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400">Error: {error}</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-4">Example Page</h1>
      <button onClick={refetch} className="btn-primary">
        Refresh
      </button>
      {/* Page content */}
    </div>
  );
}
```

## Custom Hooks

### Data Fetching Hook Pattern

```tsx
// src/hooks/useExampleData.ts
import { useState, useCallback, useEffect } from 'react';
import { fetchWithFallback, getBackendUrl, isDevMode } from '@/utils/api';

interface ExampleData {
  id: string;
  name: string;
}

// Mock data for dev mode
const mockData: ExampleData[] = [
  { id: '1', name: 'Example 1' },
  { id: '2', name: 'Example 2' },
];

export function useExampleData() {
  const [data, setData] = useState<ExampleData[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchWithFallback<ExampleData[]>(
        '/api/example',
        { credentials: 'include' },
        mockData
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  };
}
```

### Action Hook Pattern

```tsx
// src/hooks/useExampleAction.ts
import { useState, useCallback } from 'react';
import { getBackendUrl } from '@/utils/api';

export function useExampleAction() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performAction = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getBackendUrl()}/api/example/${id}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      });

      if (!response.ok) {
        throw new Error('Action failed');
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    performAction,
    isLoading,
    error,
  };
}
```

## State Management

### Authentication Context

```tsx
// Using AuthContext
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout, checkAuth } = useAuth();

  if (!isAuthenticated) {
    return <button onClick={login}>Login</button>;
  }

  return (
    <div>
      <p>Welcome, {user?.name}</p>
      <p>Regions: {user?.allowed_regions.join(', ')}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Local State

```tsx
// Component state for UI
const [isModalOpen, setIsModalOpen] = useState(false);
const [selectedItem, setSelectedItem] = useState<string | null>(null);
const [sortField, setSortField] = useState<'name' | 'date'>('name');
const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
```

## Routing

### Route Configuration

```tsx
// src/App.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <ProtectedRoute><Layout /></ProtectedRoute>,
    children: [
      { path: 'dashboard', element: <BuildOverviewPage /> },
      { path: 'preconfig', element: <PreconfigPage /> },
      { path: 'assign', element: <AssignPage /> },
      { path: 'build-logs', element: <BuildLogsPage /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

### Protected Routes

```tsx
// src/components/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="animate-spin h-8 w-8 border-4 border-green-500 rounded-full border-t-transparent" />
    </div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

## Styling

### Tailwind Classes

```tsx
// Common patterns
<div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
<button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-white">
<input className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white">
<table className="w-full text-left">
```

### Color Scheme

| Purpose | Class |
|---------|-------|
| Background | `bg-gray-900`, `bg-gray-800` |
| Text | `text-white`, `text-gray-300`, `text-gray-400` |
| Primary | `bg-green-600`, `text-green-400` |
| Error | `bg-red-600`, `text-red-400` |
| Border | `border-gray-700` |

### Responsive Design

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
```

## Type Definitions

### Defining Types

```tsx
// src/types/example.ts
export interface ExampleItem {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  createdAt: string;
  metadata?: Record<string, unknown>;
}

export interface ExampleResponse {
  items: ExampleItem[];
  total: number;
}
```

### Using Types

```tsx
import { ExampleItem, ExampleResponse } from '@/types/example';

function processItem(item: ExampleItem): string {
  return `${item.name}: ${item.status}`;
}
```

## API Communication

### Using fetchWithFallback

```tsx
import { fetchWithFallback } from '@/utils/api';

// Automatically handles dev mode fallback
const data = await fetchWithFallback<MyType>(
  '/api/endpoint',
  { credentials: 'include' },
  mockData
);
```

### Direct Fetch

```tsx
const response = await fetch(`${getBackendUrl()}/api/endpoint`, {
  method: 'POST',
  credentials: 'include',  // Always include for auth
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
});

if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}

const result = await response.json();
```

## Modal Pattern

```tsx
// src/components/ExampleModal.tsx
interface ExampleModalProps {
  item: ExampleItem;
  onClose: () => void;
}

export default function ExampleModal({ item, onClose }: ExampleModalProps) {
  // Click outside to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-gray-800 rounded-lg p-6 max-w-lg w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white">{item.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>
        {/* Modal content */}
      </div>
    </div>
  );
}
```

## Testing

### Component Testing (Future)

```tsx
// __tests__/ServerCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import ServerCard from '@/components/ServerCard';

describe('ServerCard', () => {
  it('renders server hostname', () => {
    const server = { hostname: 'test-server', percent_built: 50 };
    render(<ServerCard server={server} />);
    expect(screen.getByText('test-server')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = jest.fn();
    const server = { hostname: 'test-server', percent_built: 50 };
    render(<ServerCard server={server} onClick={onClick} />);
    fireEvent.click(screen.getByText('test-server'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

## Best Practices

### Do

- Use TypeScript strictly
- Create reusable components
- Use custom hooks for data fetching
- Handle loading and error states
- Include mock data for dev mode
- Use semantic HTML

### Don't

- Use `any` type
- Put logic in JSX
- Ignore TypeScript errors
- Skip error handling
- Forget credentials in fetch

## Next Steps

- [Backend Guide](backend-guide.md) - Backend development
- [Testing](testing.md) - Testing guide
- [Architecture: Frontend](../architecture/frontend.md) - Architecture details
