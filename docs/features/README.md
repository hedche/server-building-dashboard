# Features Overview

The Server Building Dashboard provides comprehensive tools for monitoring and managing server builds across multiple data center regions.

## Quick Navigation

| Feature | Description |
|---------|-------------|
| [Build Overview](build-overview.md) | Real-time server build monitoring |
| [Preconfig Management](preconfig-management.md) | Server preconfiguration management |
| [Server Assignment](server-assignment.md) | Assign completed servers to customers |
| [Build Logs](build-logs.md) | Search and view build logs |

## Feature Matrix

| Feature | Admin | Operator | User |
|---------|:-----:|:--------:|:----:|
| View builds (all regions) | ✓ | - | - |
| View builds (assigned regions) | ✓ | ✓ | ✓ |
| View server details | ✓ | ✓ | ✓ |
| View preconfigs | ✓ | ✓ | ✓ |
| Push preconfigs | ✓ | ✓ | - |
| Assign servers | ✓ | ✓ | - |
| View build logs | ✓ | ✓ | ✓ |

## Main Dashboard

After login, users land on the Build Overview page:

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] Server Dashboard              user@example.com [Logout]
├─────────────────────────────────────────────────────────────┤
│ ┌────────┐                                                   │
│ │ Build  │  Build Overview                                   │
│ │ Overview                                                   │
│ ├────────┤  ┌─────────────────────────────────────────────┐  │
│ │Preconfig│  │ Region: [CBG ▼]          [↻ Refresh]        │  │
│ ├────────┤  ├─────────────────────────────────────────────┤  │
│ │ Assign │  │                                              │  │
│ ├────────┤  │  Rack 1-A        Rack 1-B        Rack 1-C   │  │
│ │ Build  │  │  ┌────────┐      ┌────────┐      ┌────────┐ │  │
│ │ Logs   │  │  │ srv-001│      │ srv-004│      │        │ │  │
│ ├────────┤  │  │ [████░░] 65%  │ [██████] 100% │        │ │  │
│ │Creds   │  │  │ srv-002│      │ srv-005│      │        │ │  │
│ │        │  │  │ [█████░] 85%  │ [██████] 100% │        │ │  │
│ └────────┘  │  └────────┘      └────────┘      └────────┘ │  │
│             └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Navigation

The sidebar provides access to all features:

| Menu Item | Page | Description |
|-----------|------|-------------|
| Build Overview | /dashboard | Real-time build status |
| Preconfig | /preconfig | Preconfig management |
| Assign | /assign | Server assignment |
| Build Logs | /build-logs | Log viewer |
| Credentials | /credentials | Credentials (coming soon) |

## Region Selection

Most pages include a region selector:

```
┌─────────────────────────────────────────┐
│ Region: [▼ Select]                      │
│         ├─ CBG (Cambridge)              │
│         ├─ DUB (Dublin)                 │
│         └─ DAL (Dallas)                 │
└─────────────────────────────────────────┘
```

**Access Control:**
- Admin users see all regions
- Builder users see only their assigned regions

## Common UI Patterns

### Loading States

```
┌─────────────────────┐
│     [⟳ Loading...]  │
└─────────────────────┘
```

### Error States

```
┌─────────────────────────────────────────┐
│  ⚠ Error loading data                   │
│  Could not connect to server            │
│  [Retry]                                │
└─────────────────────────────────────────┘
```

### Empty States

```
┌─────────────────────────────────────────┐
│  No servers currently building          │
│  in this region                         │
└─────────────────────────────────────────┘
```

## Progress Indicators

Build progress uses color coding:

| Progress | Color | Meaning |
|----------|-------|---------|
| 0-99% | Blue | Building |
| 100% | Green | Complete |
| Failed | Red | Error |

## Modals

Clicking on items opens detail modals:

### Server Modal
- Basic info (hostname, DBID, serial number)
- Build progress
- Hardware specs (CPU, RAM, storage)
- Network info (IP, MAC)
- Timing (start, estimated completion, heartbeat)

### Preconfig Modal
- Preconfig details (DBID, size, region)
- Timestamps (created, pushed)
- Configuration JSON

## Data Refresh

- **Manual refresh:** Click refresh button on each page
- **No auto-refresh:** Data is fetched on page load and manual refresh
- **Real-time updates:** Not currently implemented

## Keyboard Navigation

### Build Logs Page
- **Arrow Up/Down:** Navigate search results
- **Enter:** Select highlighted result
- **Escape:** Close search results

## Dev Mode

When `VITE_DEV_MODE=true`:

```
┌─────────────────────────────────────────┐
│              Login Page                 │
│                                         │
│         [Login with SAML]               │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  🔧 Development Mode Toggle      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
                              [Dev Mode] ← Yellow button in corner
```

- Click "Dev Mode" to bypass SAML authentication
- Mock data used when backend unavailable
- Yellow indicator shows dev mode is active

## Mobile Support

The UI is responsive but optimized for desktop:
- Sidebar collapses on smaller screens
- Tables become scrollable
- Rack visualizations stack vertically

## Next Steps

- [Build Overview](build-overview.md) - Monitor builds in real-time
- [Preconfig Management](preconfig-management.md) - Manage preconfigs
- [Server Assignment](server-assignment.md) - Assign servers
- [Build Logs](build-logs.md) - View build logs
