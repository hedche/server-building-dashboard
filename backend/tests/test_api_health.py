"""
Integration tests for health and root endpoints
"""

import pytest
from datetime import datetime


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check_success(self, client):
        """Test health check returns success"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"])

    def test_health_check_no_auth_required(self, client):
        """Test health check doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.integration
class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_endpoint_success(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Server Building Dashboard API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"

    def test_root_endpoint_no_auth_required(self, client):
        """Test root endpoint doesn't require authentication"""
        response = client.get("/")
        assert response.status_code == 200
