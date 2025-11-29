"""Tests for build logs API endpoints"""
import pytest
from pathlib import Path


def test_build_log_requires_auth(client):
    """Test that build log endpoint requires authentication"""
    response = client.get("/api/build-logs/test-server-001")
    assert response.status_code == 401


def test_build_log_success(client, authenticated_user, tmp_path, monkeypatch):
    """Test successful build log retrieval"""
    # Create temp log directory with nested structure
    logs_dir = tmp_path / "build_logs"
    hostname_dir = logs_dir / "build-server-01" / "test-server-001"
    hostname_dir.mkdir(parents=True)
    log_file = hostname_dir / "test-server-001-Installer.log"
    log_content = "Sample build log content\nLine 2\nLine 3"
    log_file.write_text(log_content)

    # Mock BUILD_LOGS_DIR
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/test-server-001")
    assert response.status_code == 200
    assert response.text == log_content
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.headers["X-Build-Server"] == "build-server-01"


def test_build_log_not_found(client, authenticated_user, tmp_path, monkeypatch):
    """Test 404 when log file doesn't exist"""
    logs_dir = tmp_path / "build_logs"
    # Create nested structure with a different hostname
    hostname_dir = logs_dir / "build-server-01" / "existing-server"
    hostname_dir.mkdir(parents=True)
    log_file = hostname_dir / "existing-server-Installer.log"
    log_file.write_text("Some log content")

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
        # Path traversal may be caught by routing layer (404) or validation (400)
        assert response.status_code in [400, 404]
        if response.status_code == 400:
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
        # Invalid chars may be caught by routing layer (404) or validation (400)
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            assert "invalid" in response.json()["detail"].lower()


def test_custom_hostname_pattern(client, authenticated_user, tmp_path, monkeypatch):
    """Test that custom hostname pattern from config is respected"""
    from app import config

    # Create temp log directory
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    # Set a stricter pattern: only lowercase letters and hyphens
    monkeypatch.setattr(config.settings, 'HOSTNAME_PATTERN', r'^[a-z-]+$')

    # This should pass the custom pattern
    response = client.get("/api/build-logs/test-server")
    # Will get 404 since file doesn't exist, but validates pattern passed
    assert response.status_code == 404

    # This should fail the custom pattern (has numbers)
    response = client.get("/api/build-logs/test-server-001")
    assert response.status_code == 400
    assert "Invalid hostname format" in response.json()["detail"]


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
    hostname_dir = logs_dir / "build-server-01" / "large-server"
    hostname_dir.mkdir(parents=True)
    log_file = hostname_dir / "large-server-Installer.log"

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

    valid_hostnames = [
        "server-001",
        "cbg-srv-123",
        "test.server.com",
        "srv_123",
        "server-with-many-dashes",
        "a1b2c3",
    ]

    for hostname in valid_hostnames:
        hostname_dir = logs_dir / "build-server-01" / hostname
        hostname_dir.mkdir(parents=True)
        log_file = hostname_dir / f"{hostname}-Installer.log"
        log_file.write_text(f"Log for {hostname}")

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    for hostname in valid_hostnames:
        response = client.get(f"/api/build-logs/{hostname}")
        assert response.status_code == 200
        assert hostname in response.text
        assert response.headers["X-Build-Server"] == "build-server-01"


def test_build_log_unicode_content(client, authenticated_user, tmp_path, monkeypatch):
    """Test that UTF-8 content is properly handled"""
    logs_dir = tmp_path / "build_logs"
    hostname_dir = logs_dir / "build-server-01" / "unicode-server"
    hostname_dir.mkdir(parents=True)
    log_file = hostname_dir / "unicode-server-Installer.log"

    unicode_content = "Build log with émojis 🚀 and spëcial çharacters"
    log_file.write_text(unicode_content, encoding='utf-8')

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/unicode-server")
    assert response.status_code == 200
    assert "🚀" in response.text
    assert response.headers["X-Build-Server"] == "build-server-01"


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


def test_build_log_multiple_build_servers_first_match(client, authenticated_user, tmp_path, monkeypatch):
    """Test that first build_server match is returned when hostname exists in multiple directories"""
    logs_dir = tmp_path / "build_logs"

    # Create same hostname in multiple build servers
    # Alpha comes first alphabetically
    alpha_dir = logs_dir / "alpha-server" / "test-host"
    alpha_dir.mkdir(parents=True)
    alpha_log = alpha_dir / "test-host-Installer.log"
    alpha_log.write_text("Log from alpha server")

    # Zebra comes last alphabetically
    zebra_dir = logs_dir / "zebra-server" / "test-host"
    zebra_dir.mkdir(parents=True)
    zebra_log = zebra_dir / "test-host-Installer.log"
    zebra_log.write_text("Log from zebra server")

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/test-host")

    # Should return first match (alphabetically)
    assert response.status_code == 200
    assert response.text == "Log from alpha server"
    assert response.headers["X-Build-Server"] == "alpha-server"


def test_build_log_build_server_discovery(client, authenticated_user, tmp_path, monkeypatch):
    """Test that logs are found across different build servers"""
    logs_dir = tmp_path / "build_logs"

    # Create different hostnames in different build_server directories
    host_a_dir = logs_dir / "build-server-01" / "host-a"
    host_a_dir.mkdir(parents=True)
    (host_a_dir / "host-a-Installer.log").write_text("Log A")

    host_b_dir = logs_dir / "build-server-02" / "host-b"
    host_b_dir.mkdir(parents=True)
    (host_b_dir / "host-b-Installer.log").write_text("Log B")

    host_c_dir = logs_dir / "build-server-03" / "host-c"
    host_c_dir.mkdir(parents=True)
    (host_c_dir / "host-c-Installer.log").write_text("Log C")

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    # Test each hostname returns correct build_server in header
    response_a = client.get("/api/build-logs/host-a")
    assert response_a.status_code == 200
    assert response_a.headers["X-Build-Server"] == "build-server-01"
    assert response_a.text == "Log A"

    response_b = client.get("/api/build-logs/host-b")
    assert response_b.status_code == 200
    assert response_b.headers["X-Build-Server"] == "build-server-02"
    assert response_b.text == "Log B"

    response_c = client.get("/api/build-logs/host-c")
    assert response_c.status_code == 200
    assert response_c.headers["X-Build-Server"] == "build-server-03"
    assert response_c.text == "Log C"


def test_build_log_hostname_dir_exists_no_log_file(client, authenticated_user, tmp_path, monkeypatch):
    """Test when hostname directory exists but -Installer.log file missing"""
    logs_dir = tmp_path / "build_logs"

    # Create hostname directory without -Installer.log file
    hostname_dir = logs_dir / "build-server-01" / "test-server"
    hostname_dir.mkdir(parents=True)
    # Intentionally do NOT create the -Installer.log file

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/test-server")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_build_log_empty_build_logs_dir(client, authenticated_user, tmp_path, monkeypatch):
    """Test when BUILD_LOGS_DIR exists but has no build_server subdirectories"""
    logs_dir = tmp_path / "build_logs"
    logs_dir.mkdir()
    # Create empty directory with no build_server subdirectories

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/any-hostname")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_build_log_header_special_characters(client, authenticated_user, tmp_path, monkeypatch):
    """Test X-Build-Server header with various build_server directory names"""
    logs_dir = tmp_path / "build_logs"

    # Test with names like: "build-server-01", "build_server_02"
    test_cases = [
        ("build-server-01", "test-host-1"),
        ("build_server_02", "test-host-2"),
        ("BuildServer03", "test-host-3"),
    ]

    for build_server, hostname in test_cases:
        hostname_dir = logs_dir / build_server / hostname
        hostname_dir.mkdir(parents=True)
        log_file = hostname_dir / f"{hostname}-Installer.log"
        log_file.write_text(f"Log from {build_server}")

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    # Assert header values match directory names
    for build_server, hostname in test_cases:
        response = client.get(f"/api/build-logs/{hostname}")
        assert response.status_code == 200
        assert response.headers["X-Build-Server"] == build_server


def test_build_log_search_order_deterministic(client, authenticated_user, tmp_path, monkeypatch):
    """Test that build_server iteration order is deterministic (alphabetical)"""
    logs_dir = tmp_path / "build_logs"

    # Create multiple build servers with same hostname
    # Create zebra first to verify it's not just file creation order
    zebra_dir = logs_dir / "zebra-server" / "host1"
    zebra_dir.mkdir(parents=True)
    (zebra_dir / "host1-Installer.log").write_text("zebra")

    alpha_dir = logs_dir / "alpha-server" / "host1"
    alpha_dir.mkdir(parents=True)
    (alpha_dir / "host1-Installer.log").write_text("alpha")

    monkeypatch.setattr("app.routers.buildlogs.settings.BUILD_LOGS_DIR", str(logs_dir))

    response = client.get("/api/build-logs/host1")

    # Should return alphabetically first build_server (alpha)
    assert response.status_code == 200
    assert response.headers["X-Build-Server"] == "alpha-server"
    assert response.text == "alpha"
