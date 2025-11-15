"""
Unit tests for Pydantic models
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from app.models import (
    User,
    Server,
    ServerDetails,
    BuildStatus,
    PreconfigData,
    PushPreconfigRequest,
    AssignRequest,
    ServerStatus,
    AssignedStatus,
)


@pytest.mark.unit
class TestUser:
    """Tests for User model"""

    def test_user_creation_valid(self):
        """Test creating a valid user"""
        user = User(
            id="test@example.com",
            email="test@example.com",
            name="Test User",
            role="user",
            groups=["Dashboard-Users"],
        )
        assert user.id == "test@example.com"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == "user"
        assert user.groups == ["Dashboard-Users"]

    def test_user_creation_minimal(self):
        """Test creating user with minimal required fields"""
        user = User(id="test@example.com", email="test@example.com")
        assert user.id == "test@example.com"
        assert user.email == "test@example.com"
        assert user.name is None
        assert user.role == "user"
        assert user.groups == []

    def test_user_invalid_email(self):
        """Test user creation with invalid email"""
        with pytest.raises(ValidationError):
            User(id="test", email="invalid-email", role="user")


@pytest.mark.unit
class TestServer:
    """Tests for Server model"""

    def test_server_creation_valid(self):
        """Test creating a valid server"""
        server = Server(
            rackID="1-E",
            hostname="test-server-001",
            dbid="100001",
            serial_number="SN-TEST-001",
            percent_built=75,
            assigned_status="not assigned",
            machine_type="Server",
            status="installing",
        )
        assert server.rackID == "1-E"
        assert server.hostname == "test-server-001"
        assert server.percent_built == 75

    def test_server_percent_built_validation_valid(self):
        """Test percent_built accepts values 0-100"""
        for percent in [0, 50, 100]:
            server = Server(
                rackID="1-E",
                hostname="test",
                dbid="1",
                serial_number="SN-1",
                percent_built=percent,
            )
            assert server.percent_built == percent

    def test_server_percent_built_validation_invalid(self):
        """Test percent_built rejects values outside 0-100"""
        with pytest.raises(ValidationError) as exc_info:
            Server(
                rackID="1-E",
                hostname="test",
                dbid="1",
                serial_number="SN-1",
                percent_built=101,
            )
        assert "percent_built" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Server(
                rackID="1-E",
                hostname="test",
                dbid="1",
                serial_number="SN-1",
                percent_built=-1,
            )
        assert "percent_built" in str(exc_info.value)

    def test_server_default_values(self):
        """Test server default values"""
        server = Server(
            rackID="1-E",
            hostname="test",
            dbid="1",
            serial_number="SN-1",
            percent_built=50,
        )
        assert server.assigned_status == "not assigned"
        assert server.machine_type == "Server"
        assert server.status == "installing"


@pytest.mark.unit
class TestServerDetails:
    """Tests for ServerDetails model"""

    def test_server_details_creation(self):
        """Test creating server details with extended fields"""
        details = ServerDetails(
            rackID="1-E",
            hostname="test-server",
            dbid="1",
            serial_number="SN-1",
            percent_built=50,
            ip_address="192.168.1.100",
            mac_address="00:1A:2B:3C:4D:5E",
            cpu_model="Intel Xeon",
            ram_gb=128,
            storage_gb=4000,
            install_start_time=datetime.utcnow(),
            estimated_completion=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
        )
        assert details.ip_address == "192.168.1.100"
        assert details.ram_gb == 128


@pytest.mark.unit
class TestBuildStatus:
    """Tests for BuildStatus model"""

    def test_build_status_creation_empty(self):
        """Test creating build status with empty regions"""
        status = BuildStatus()
        assert status.cbg == []
        assert status.dub == []
        assert status.dal == []

    def test_build_status_creation_with_servers(self):
        """Test creating build status with servers"""
        server = Server(
            rackID="1-E",
            hostname="test",
            dbid="1",
            serial_number="SN-1",
            percent_built=50,
        )
        status = BuildStatus(cbg=[server], dub=[], dal=[])
        assert len(status.cbg) == 1
        assert status.cbg[0].hostname == "test"


@pytest.mark.unit
class TestPreconfigData:
    """Tests for PreconfigData model"""

    def test_preconfig_creation_valid(self):
        """Test creating valid preconfig"""
        preconfig = PreconfigData(
            id="pre-001",
            depot=1,
            config={"os": "Ubuntu 22.04"},
            created_at=datetime.utcnow(),
        )
        assert preconfig.id == "pre-001"
        assert preconfig.depot == 1
        assert preconfig.config == {"os": "Ubuntu 22.04"}

    def test_preconfig_depot_validation_valid(self):
        """Test depot validation accepts valid values"""
        for depot in [1, 2, 4]:
            preconfig = PreconfigData(
                id="pre-001", depot=depot, config={}, created_at=datetime.utcnow()
            )
            assert preconfig.depot == depot

    def test_preconfig_depot_validation_invalid(self):
        """Test depot validation rejects invalid values"""
        with pytest.raises(ValidationError) as exc_info:
            PreconfigData(
                id="pre-001", depot=3, config={}, created_at=datetime.utcnow()
            )
        assert "depot must be one of [1, 2, 4]" in str(exc_info.value)


@pytest.mark.unit
class TestPushPreconfigRequest:
    """Tests for PushPreconfigRequest model"""

    def test_push_preconfig_request_valid(self):
        """Test creating valid push preconfig request"""
        for depot in [1, 2, 4]:
            request = PushPreconfigRequest(depot=depot)
            assert request.depot == depot

    def test_push_preconfig_request_invalid(self):
        """Test push preconfig request with invalid depot"""
        with pytest.raises(ValidationError) as exc_info:
            PushPreconfigRequest(depot=5)
        assert "depot must be one of [1, 2, 4]" in str(exc_info.value)


@pytest.mark.unit
class TestAssignRequest:
    """Tests for AssignRequest model"""

    def test_assign_request_valid(self):
        """Test creating valid assign request"""
        request = AssignRequest(
            serial_number="SN-001", hostname="test-server", dbid="100001"
        )
        assert request.serial_number == "SN-001"
        assert request.hostname == "test-server"
        assert request.dbid == "100001"

    def test_assign_request_empty_fields(self):
        """Test assign request rejects empty fields"""
        with pytest.raises(ValidationError):
            AssignRequest(serial_number="", hostname="test", dbid="1")


@pytest.mark.unit
class TestEnums:
    """Tests for enum models"""

    def test_server_status_enum_values(self):
        """Test ServerStatus enum values"""
        assert ServerStatus.INSTALLING == "installing"
        assert ServerStatus.COMPLETE == "complete"
        assert ServerStatus.FAILED == "failed"

    def test_assigned_status_enum_values(self):
        """Test AssignedStatus enum values"""
        assert AssignedStatus.ASSIGNED == "assigned"
        assert AssignedStatus.NOT_ASSIGNED == "not assigned"
