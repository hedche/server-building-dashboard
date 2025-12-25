# Testing Guide

Complete guide for testing the Server Building Dashboard.

## Overview

| Component | Framework | Coverage |
|-----------|-----------|----------|
| Backend | pytest | Yes |
| Frontend | (Not implemented) | - |
| E2E | (Not implemented) | - |

## Backend Testing

### Test Environment

Tests run in a Docker container matching the production environment:

```bash
# Build test image
cd backend
docker build -t server-dashboard-backend-test:latest .
```

### Running Tests

```bash
# All tests
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v

# Specific test file
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_auth.py -v

# Specific test
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest tests/test_auth.py::TestSAMLAuth::test_extract_user_data -v

# With coverage
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
  -v "$(pwd)/.env.example:/app/.env:ro" \
  server-dashboard-backend-test:latest \
  pytest -v --cov=app --cov=main --cov-report=term-missing
```

### Local Testing (with venv)

```bash
cd backend
source venv/bin/activate

# Run tests
pytest -v

# With coverage
pytest -v --cov=app --cov=main --cov-report=term-missing

# Generate HTML report
pytest -v --cov=app --cov=main --cov-report=html
```

## Test Structure

### Directory Layout

```
backend/
└── tests/
    ├── __init__.py
    ├── conftest.py           # Shared fixtures
    ├── test_auth.py          # Authentication tests
    ├── test_build_history.py # Build endpoint tests
    ├── test_preconfig.py     # Preconfig tests
    ├── test_assign.py        # Assignment tests
    └── test_buildlogs.py     # Build logs tests
```

### conftest.py

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from app.models import User

@pytest.fixture
def client():
    """Unauthenticated test client."""
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return User(
        id="test@example.com",
        email="test@example.com",
        name="Test User",
        role="admin",
        groups=["Dashboard-Admins"],
        is_admin=True,
        allowed_regions=["cbg", "dub", "dal"]
    )

@pytest.fixture
def authenticated_client(client, mock_user):
    """Authenticated test client."""
    with patch('app.auth.get_current_user', return_value=mock_user):
        yield client

@pytest.fixture
def builder_client(client):
    """Builder-level authenticated client."""
    builder_user = User(
        id="builder@example.com",
        email="builder@example.com",
        name="Builder User",
        role="operator",
        groups=["Dashboard-Operators"],
        is_admin=False,
        allowed_regions=["cbg"]
    )
    with patch('app.auth.get_current_user', return_value=builder_user):
        yield client
```

## Writing Tests

### Basic Test Pattern

```python
# tests/test_example.py
import pytest

class TestExampleEndpoint:
    """Tests for /api/example endpoint."""

    def test_get_example_authenticated(self, authenticated_client):
        """Test successful request with authentication."""
        response = authenticated_client.get("/api/example")
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data

    def test_get_example_unauthenticated(self, client):
        """Test request without authentication returns 401."""
        response = client.get("/api/example")
        assert response.status_code == 401

    def test_get_example_unauthorized(self, builder_client):
        """Test request with insufficient permissions."""
        response = builder_client.get("/api/admin-only")
        assert response.status_code == 403
```

### Testing POST Endpoints

```python
def test_create_item(self, authenticated_client):
    """Test creating an item."""
    payload = {
        "name": "Test Item",
        "value": 123
    }

    response = authenticated_client.post(
        "/api/items",
        json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["status"] == "success"
```

### Testing Validation

```python
def test_invalid_input(self, authenticated_client):
    """Test validation of invalid input."""
    payload = {
        "name": "",  # Invalid: empty string
        "value": -1  # Invalid: negative
    }

    response = authenticated_client.post(
        "/api/items",
        json=payload
    )

    assert response.status_code == 422  # Validation error

def test_missing_required_field(self, authenticated_client):
    """Test missing required field."""
    payload = {
        # name is required but missing
        "value": 123
    }

    response = authenticated_client.post(
        "/api/items",
        json=payload
    )

    assert response.status_code == 422
```

### Testing with Mocks

```python
from unittest.mock import patch, MagicMock, AsyncMock

def test_external_api_call(self, authenticated_client):
    """Test endpoint that calls external API."""
    with patch('app.routers.example.external_api') as mock_api:
        mock_api.return_value = {"result": "success"}

        response = authenticated_client.get("/api/external")

        assert response.status_code == 200
        mock_api.assert_called_once()

def test_database_query(self, authenticated_client):
    """Test endpoint with database query."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(
            all=MagicMock(return_value=[])
        ))
    ))

    with patch('app.database.get_db', return_value=mock_db):
        response = authenticated_client.get("/api/items")
        assert response.status_code == 200
```

### Testing Error Scenarios

```python
def test_not_found(self, authenticated_client):
    """Test 404 response for missing resource."""
    response = authenticated_client.get("/api/items/nonexistent")
    assert response.status_code == 404

def test_server_error(self, authenticated_client):
    """Test handling of server errors."""
    with patch('app.routers.example.get_data') as mock:
        mock.side_effect = Exception("Database error")

        response = authenticated_client.get("/api/items")
        assert response.status_code == 500
```

## Test Categories

### Unit Tests

Test individual functions:

```python
from app.permissions import get_user_permissions, check_region_access

def test_get_user_permissions_admin():
    """Test admin user gets all regions."""
    is_admin, regions = get_user_permissions("admin@example.com")
    assert is_admin is True
    assert len(regions) > 0

def test_check_region_access():
    """Test region access check."""
    assert check_region_access("admin@example.com", "cbg") is True
    assert check_region_access("unknown@example.com", "cbg") is False
```

### Integration Tests

Test endpoint behavior:

```python
def test_full_assignment_flow(self, authenticated_client):
    """Test complete assignment workflow."""
    # Get unassigned servers
    response = authenticated_client.get("/api/build-history/cbg")
    servers = response.json()["servers"]

    # Assign a server
    unassigned = [s for s in servers if s["assigned_status"] == "not assigned"]
    if unassigned:
        server = unassigned[0]
        assign_response = authenticated_client.post(
            "/api/assign",
            json={
                "serial_number": server["serial_number"],
                "hostname": server["hostname"],
                "dbid": server["dbid"]
            }
        )
        assert assign_response.status_code == 200
```

## Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| Routers | 80% | - |
| Auth | 90% | - |
| Models | 100% | - |
| Permissions | 90% | - |
| Overall | 80% | - |

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build test image
        run: |
          cd backend
          docker build -t server-dashboard-backend-test:latest .

      - name: Run tests
        run: |
          cd backend
          docker run --rm \
            -v "$(pwd)/tests:/app/tests:ro" \
            -v "$(pwd)/saml_metadata:/app/saml_metadata:ro" \
            -v "$(pwd)/.env.example:/app/.env:ro" \
            server-dashboard-backend-test:latest \
            pytest -v --cov=app --cov=main --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml
```

## Frontend Testing (Future)

### Recommended Stack

| Tool | Purpose |
|------|---------|
| Jest | Test runner |
| React Testing Library | Component testing |
| MSW | API mocking |
| Cypress | E2E testing |

### Example Component Test

```tsx
// __tests__/ServerCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import ServerCard from '@/components/ServerCard';

describe('ServerCard', () => {
  const mockServer = {
    hostname: 'test-server',
    dbid: '123',
    percent_built: 75,
    status: 'installing'
  };

  it('renders server information', () => {
    render(<ServerCard server={mockServer} />);

    expect(screen.getByText('test-server')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('calls onClick handler', () => {
    const onClick = jest.fn();
    render(<ServerCard server={mockServer} onClick={onClick} />);

    fireEvent.click(screen.getByText('test-server'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

## Troubleshooting Tests

### Test Isolation

Ensure tests don't affect each other:

```python
@pytest.fixture(autouse=True)
def reset_state():
    """Reset any global state before each test."""
    yield
    # Cleanup after test
```

### Async Tests

Use pytest-asyncio for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

### Debugging Tests

```bash
# Run with print output
pytest -v -s

# Stop on first failure
pytest -v -x

# Run only failed tests
pytest -v --lf

# Enable debugging
pytest -v --pdb
```

## Next Steps

- [Frontend Guide](frontend-guide.md) - Frontend development
- [Backend Guide](backend-guide.md) - Backend development
- [Contributing](contributing.md) - Contribution guidelines
