# Build Endpoints

API endpoints for retrieving server build status and history.

## Overview

| Endpoint | Description |
|----------|-------------|
| `GET /api/build-status` | Current active builds |
| `GET /api/build-history/{region}` | Today's build history |
| `GET /api/build-history/{region}/{date}` | Historical builds |

---

## Get Build Status

Retrieve currently building servers across all regions.

```http
GET /api/build-status
```

### Request

No parameters required.

**Headers:**
- `Cookie: session_token=...` (required)

### Response

```json
{
  "cbg": [
    {
      "rackID": "1-E",
      "hostname": "cbg-srv-001",
      "dbid": "100001",
      "serial_number": "SN-CBG-001",
      "percent_built": 55,
      "assigned_status": "not assigned",
      "machine_type": "Server",
      "status": "installing"
    },
    {
      "rackID": "2-A",
      "hostname": "cbg-srv-002",
      "dbid": "100002",
      "serial_number": "SN-CBG-002",
      "percent_built": 100,
      "assigned_status": "assigned",
      "machine_type": "Server",
      "status": "complete"
    }
  ],
  "dub": [
    {
      "rackID": "1-A",
      "hostname": "dub-srv-001",
      "dbid": "200001",
      "serial_number": "SN-DUB-001",
      "percent_built": 30,
      "assigned_status": "not assigned",
      "machine_type": "Server",
      "status": "installing"
    }
  ],
  "dal": []
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `{region}` | array | Array of servers for each region |

**Server Object:**

| Field | Type | Description |
|-------|------|-------------|
| `rackID` | string | Rack identifier (e.g., "1-E", "S1-A") |
| `hostname` | string | Server hostname |
| `dbid` | string | Database identifier |
| `serial_number` | string | Hardware serial number |
| `percent_built` | integer | Build progress (0-100) |
| `assigned_status` | string | "assigned" or "not assigned" |
| `machine_type` | string | Server type |
| `status` | string | "installing", "complete", or "failed" |

### Permission Filtering

- **Admin users:** See all regions
- **Builder users:** See only allowed regions

### Example

```bash
curl -b cookies.txt http://localhost:8000/api/build-status
```

```javascript
const response = await fetch('/api/build-status', {
  credentials: 'include'
});
const buildStatus = await response.json();

// Access servers for a specific region
const cbgServers = buildStatus.cbg;
```

### Errors

| Status | Description |
|--------|-------------|
| 401 | Unauthorized - invalid session |

---

## Get Today's Build History

Retrieve build history for the current day.

```http
GET /api/build-history/{region}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `region` | string | Yes | Region code: `cbg`, `dub`, or `dal` |

### Response

```json
{
  "region": "cbg",
  "date": "2025-01-01",
  "servers": [
    {
      "id": 1,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "hostname": "cbg-srv-001",
      "rack_id": "1-E",
      "dbid": "100001",
      "serial_number": "SN-CBG-001",
      "machine_type": "Server",
      "bundle": null,
      "ip_address": "192.168.1.100",
      "mac_address": "00:1A:2B:3C:4D:5E",
      "build_server": "cbg-build-01",
      "percent_built": 100,
      "build_status": "complete",
      "assigned_status": "assigned",
      "build_start": "2025-01-01T10:00:00",
      "build_end": "2025-01-01T11:30:00",
      "assigned_by": "operator@example.com",
      "assigned_at": "2025-01-01T11:35:00",
      "created_at": "2025-01-01T10:00:00",
      "updated_at": "2025-01-01T11:35:00"
    }
  ]
}
```

### Response Fields

**BuildHistoryResponse:**

| Field | Type | Description |
|-------|------|-------------|
| `region` | string | Region code |
| `date` | string | Date in YYYY-MM-DD format |
| `servers` | array | Array of build records |

**BuildHistoryRecord:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Database record ID |
| `uuid` | string | Unique identifier |
| `hostname` | string | Server hostname |
| `rack_id` | string | Rack identifier |
| `dbid` | string | Database identifier |
| `serial_number` | string | Hardware serial |
| `machine_type` | string | Server type |
| `bundle` | string | Bundle identifier (optional) |
| `ip_address` | string | IP address |
| `mac_address` | string | MAC address |
| `build_server` | string | Build server hostname |
| `percent_built` | integer | Build progress (0-100) |
| `build_status` | string | Build status |
| `assigned_status` | string | Assignment status |
| `build_start` | datetime | Build start time |
| `build_end` | datetime | Build end time (optional) |
| `assigned_by` | string | Assigner email (optional) |
| `assigned_at` | datetime | Assignment time (optional) |
| `created_at` | datetime | Record creation time |
| `updated_at` | datetime | Last update time |

### Example

```bash
curl -b cookies.txt http://localhost:8000/api/build-history/cbg
```

```javascript
const response = await fetch('/api/build-history/cbg', {
  credentials: 'include'
});
const history = await response.json();

console.log(`${history.servers.length} builds on ${history.date}`);
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid region code |
| 401 | Unauthorized |
| 403 | User doesn't have access to this region |

---

## Get Historical Build Data

Retrieve build history for a specific date.

```http
GET /api/build-history/{region}/{date}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `region` | string | Yes | Region code: `cbg`, `dub`, or `dal` |
| `date` | string | Yes | Date in YYYY-MM-DD format |

### Response

Same as [Get Today's Build History](#get-todays-build-history).

### Example

```bash
# Get builds from December 25, 2024
curl -b cookies.txt http://localhost:8000/api/build-history/cbg/2024-12-25
```

```javascript
const date = '2024-12-25';
const response = await fetch(`/api/build-history/cbg/${date}`, {
  credentials: 'include'
});
const history = await response.json();
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid region or date format |
| 401 | Unauthorized |
| 403 | User doesn't have access to this region |

---

## Region Codes

| Code | Name | Depot ID |
|------|------|----------|
| `cbg` | Cambridge | 1 |
| `dub` | Dublin | 2 |
| `dal` | Dallas | 4 |

---

## Frontend Hook Usage

### useBuildStatus

```typescript
import { useBuildStatus } from '@/hooks/useBuildStatus';

function BuildOverview() {
  const { buildStatus, isLoading, error, refetch } = useBuildStatus();

  if (isLoading) return <Loading />;
  if (error) return <Error message={error} />;

  const cbgServers = buildStatus?.cbg ?? [];

  return (
    <div>
      <button onClick={refetch}>Refresh</button>
      <RackVisualization servers={cbgServers} />
    </div>
  );
}
```

### useBuildHistory

```typescript
import { useBuildHistory } from '@/hooks/useBuildHistory';

function AssignmentPage() {
  const [selectedDate, setSelectedDate] = useState('2025-01-01');
  const { buildHistory, isLoading, error, refetch } = useBuildHistory();

  // buildHistory is keyed by region
  const cbgHistory = buildHistory?.cbg ?? [];

  // Filter for unassigned servers
  const unassigned = cbgHistory.filter(
    s => s.assigned_status === 'not assigned'
  );

  return <AssignmentTable servers={unassigned} />;
}
```

---

## Next Steps

- [Server Endpoints](server-endpoints.md) - Server details and assignment
- [Architecture: Data Flow](../architecture/data-flow.md) - Request patterns
- [Features: Build Overview](../features/build-overview.md) - Feature guide
