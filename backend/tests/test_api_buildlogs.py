"""Tests for build logs API endpoints"""
import pytest
from pathlib import Path


def test_build_log_requires_auth(client):
    """Test that build log endpoint requires authentication"""
    response = client.get("/api/build-logs/test-server-001")
    assert response.status_code == 401


def test_build_log_success(client, authenticated_user, tmp_path, monkeypatch):
    """Test successful build log retrieval"""
    # Create temp log directory with sample log
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    log_file = logs_dir / "test-server-001.log"
    log_content = "Sample build log content\nLine 2\nLine 3"
    log_file.write_text(log_content)

    # Mock BUILD_LOGS_DIR
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/test-server-001")
    assert response.status_code == 200
    assert response.text == log_content
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_build_log_not_found(client, authenticated_user, tmp_path, monkeypatch):
    """Test 404 when log file doesn't exist"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/nonexistent-server")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_build_log_path_traversal_prevention(client, authenticated_user, tmp_path, monkeypatch):
    """Test that path traversal attempts are blocked"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    # Test various path traversal attempts
    traversal_attempts = [
        "../../../etc/passwd",
        "..%2F..%2Fetc%2Fpasswd",
        "....//....//etc/passwd",
        "test/../../etc/passwd",
    ]

    for attempt in traversal_attempts:
        response = client.get(f"/api/build-logs/{attempt}")
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


def test_build_log_invalid_characters(client, authenticated_user, tmp_path, monkeypatch):
    """Test that invalid characters in hostname are rejected"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    invalid_hostnames = [
        "server@123",
        "server#123",
        "server%123",
        "server/123",
        "server\\123",
    ]

    for hostname in invalid_hostnames:
        response = client.get(f"/api/build-logs/{hostname}")
        assert response.status_code == 400


def test_build_log_empty_hostname(client, authenticated_user):
    """Test that empty hostname is handled"""
    response = client.get("/api/build-logs/")
    assert response.status_code in [404, 405]  # Depends on router config


def test_build_log_directory_not_configured(client, authenticated_user, monkeypatch):
    """Test when BUILD_LOGS_DIR is not configured"""
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", None)

    response = client.get("/api/build-logs/test-server")
    assert response.status_code == 500
    assert "not configured" in response.json()["detail"].lower()


def test_build_log_large_file(client, authenticated_user, tmp_path, monkeypatch):
    """Test that very large files are rejected"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    log_file = logs_dir / "large-server.log"

    # Create file larger than 10MB limit
    large_content = "A" * (11 * 1024 * 1024)
    log_file.write_text(large_content)

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/large-server")
    assert response.status_code == 500
    assert "too large" in response.json()["detail"].lower()


def test_build_log_valid_hostnames(client, authenticated_user, tmp_path, monkeypatch):
    """Test that valid hostname formats are accepted"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()

    valid_hostnames = [
        "server-001",
        "cbg-srv-123",
        "test.server.com",
        "srv_123",
        "server-with-many-dashes",
        "a1b2c3",
    ]

    for hostname in valid_hostnames:
        log_file = logs_dir / f"{hostname}.log"
        log_file.write_text(f"Log for {hostname}")

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    for hostname in valid_hostnames:
        response = client.get(f"/api/build-logs/{hostname}")
        assert response.status_code == 200
        assert hostname in response.text


def test_build_log_unicode_content(client, authenticated_user, tmp_path, monkeypatch):
    """Test that UTF-8 content is properly handled"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    log_file = logs_dir / "unicode-server.log"

    unicode_content = "Build log with émojis 🚀 and spëcial çharacters"
    log_file.write_text(unicode_content, encoding='utf-8')

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/unicode-server")
    assert response.status_code == 200
    assert "🚀" in response.text


def test_build_log_hostname_length_validation(client, authenticated_user, tmp_path, monkeypatch):
    """Test hostname length limits"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    # Test hostname that's too long (>255 characters)
    long_hostname = "a" * 256
    response = client.get(f"/api/build-logs/{long_hostname}")
    assert response.status_code == 400
    assert "length" in response.json()["detail"].lower()


def test_build_log_directory_doesnt_exist(client, authenticated_user, tmp_path, monkeypatch):
    """Test when BUILD_LOGS_DIR directory doesn't exist"""
    nonexistent_dir = tmp_path / "nonexistent_logs"
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(nonexistent_dir))

    response = client.get("/api/build-logs/test-server")
    # Should return 404 because the file doesn't exist (directory doesn't exist)
    assert response.status_code in [404, 500]
