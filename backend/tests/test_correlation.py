"""
Tests for correlation ID functionality
"""

import pytest
from app.correlation import (
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    correlation_id_var,
)


class TestCorrelationIdContext:
    """Unit tests for correlation ID context management"""

    def test_generate_correlation_id_format(self):
        """Correlation ID should be valid UUID format"""
        cid = generate_correlation_id()
        assert len(cid) == 36  # UUID format: 8-4-4-4-12
        assert cid.count("-") == 4

    def test_generate_correlation_id_unique(self):
        """Each generated correlation ID should be unique"""
        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_set_and_get_correlation_id(self):
        """Should be able to set and retrieve correlation ID"""
        test_id = "test-correlation-id-123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id

    def test_get_correlation_id_default(self):
        """Should return None when no correlation ID is set"""
        # Reset the context var
        correlation_id_var.set(None)
        assert get_correlation_id() is None


class TestCorrelationIdMiddleware:
    """Integration tests for correlation ID in requests"""

    def test_request_generates_correlation_id(self, client, authenticated_user):
        """Requests without X-Request-ID should generate one"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        # Verify UUID format
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36
        assert request_id.count("-") == 4

    def test_request_uses_provided_correlation_id(self, client, authenticated_user):
        """Requests with X-Request-ID should use that value"""
        custom_id = "custom-request-id-456"
        response = client.get("/api/health", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == custom_id

    def test_correlation_id_different_per_request(self, client, authenticated_user):
        """Each request should get a unique correlation ID"""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")

        id1 = response1.headers.get("X-Request-ID")
        id2 = response2.headers.get("X-Request-ID")

        assert id1 is not None
        assert id2 is not None
        assert id1 != id2

    def test_correlation_id_on_unauthenticated_endpoint(self, client):
        """Correlation ID should work on endpoints that don't require auth"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_correlation_id_preserved_across_request(self, client, authenticated_user):
        """Provided correlation ID should be returned unchanged"""
        # Test with a UUID-like format
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get("/api/health", headers={"X-Request-ID": test_uuid})
        assert response.headers.get("X-Request-ID") == test_uuid

        # Test with a custom format
        test_custom = "my-custom-id-12345"
        response = client.get("/api/health", headers={"X-Request-ID": test_custom})
        assert response.headers.get("X-Request-ID") == test_custom
