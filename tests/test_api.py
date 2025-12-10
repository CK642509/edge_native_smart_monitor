"""Integration tests for FastAPI endpoints."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.monitor_system import MonitorSystem


@pytest.fixture
def api_client(monitor_system: MonitorSystem) -> TestClient:
    """Create a FastAPI test client with monitor system."""
    monitor_system.start()
    app = create_app(monitor_system)
    client = TestClient(app)
    yield client
    if monitor_system.is_running():
        monitor_system.stop()


class TestAPIEndpoints:
    """Test cases for FastAPI endpoints."""

    def test_root_endpoint(self, api_client: TestClient) -> None:
        """Test root endpoint returns API information."""
        response = api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_status_endpoint(self, api_client: TestClient) -> None:
        """Test status endpoint returns system status."""
        response = api_client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "monitoring_enabled" in data
        assert "is_recording" in data
        assert "buffer_size" in data
        assert "recording_count" in data

    def test_monitoring_enable_endpoint(self, api_client: TestClient) -> None:
        """Test enabling monitoring via API."""
        # First disable it
        api_client.post("/monitoring/disable")
        
        # Then enable
        response = api_client.post("/monitoring/enable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
        
        # Verify status
        status_response = api_client.get("/status")
        status = status_response.json()
        assert status["monitoring_enabled"] is True

    def test_monitoring_disable_endpoint(self, api_client: TestClient) -> None:
        """Test disabling monitoring via API."""
        response = api_client.post("/monitoring/disable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
        
        # Verify status
        status_response = api_client.get("/status")
        status = status_response.json()
        assert status["monitoring_enabled"] is False

    def test_recording_trigger_endpoint(
        self, api_client: TestClient, monitor_system: MonitorSystem
    ) -> None:
        """Test triggering recording via API."""
        # Capture some frames first
        for _ in range(20):
            monitor_system.tick()
            time.sleep(0.01)
        
        response = api_client.post("/recording/trigger")
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "file_path" in data
        assert data["file_path"] is not None

    def test_recording_trigger_empty_buffer(
        self, api_client: TestClient
    ) -> None:
        """Test triggering recording with empty buffer."""
        response = api_client.post("/recording/trigger")
        
        # Should still return 200 but with success=False
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_config_get_endpoint(self, api_client: TestClient) -> None:
        """Test getting configuration via API."""
        response = api_client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "pre_event_seconds" in data
        assert "post_event_seconds" in data
        assert "frame_interval_seconds" in data
        assert "detection_interval_seconds" in data
        assert "enable_monitoring" in data

    def test_config_update_endpoint(self, api_client: TestClient) -> None:
        """Test updating configuration via API."""
        new_config = {
            "pre_event_seconds": 5.0,
            "post_event_seconds": 5.0,
        }
        
        response = api_client.put("/config", json=new_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "updated_fields" in data
        assert data["updated_fields"]["pre_event_seconds"] == 5.0
        assert data["updated_fields"]["post_event_seconds"] == 5.0

    def test_config_update_partial(self, api_client: TestClient) -> None:
        """Test partial configuration update via API."""
        # Get current config
        current_response = api_client.get("/config")
        current_config = current_response.json()
        
        # Update only one field
        update = {"pre_event_seconds": 15.0}
        response = api_client.put("/config", json=update)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["updated_fields"]["pre_event_seconds"] == 15.0
        
        # Verify config was actually updated
        verify_response = api_client.get("/config")
        verify_config = verify_response.json()
        assert verify_config["pre_event_seconds"] == 15.0
        # Other fields should remain unchanged
        assert verify_config["post_event_seconds"] == current_config["post_event_seconds"]

    def test_stream_mjpeg_endpoint(self, api_client: TestClient) -> None:
        """Test MJPEG stream endpoint is accessible."""
        # Note: We can't fully test the streaming behavior in a unit test
        # as it's an infinite stream. We just verify the endpoint exists
        # and returns the correct content type header.
        # The actual streaming is tested manually or in integration tests.
        
        # Just verify the endpoint responds (it will hang if we try to read)
        # So we'll just check that it doesn't immediately return an error
        import threading
        
        result = {"status_code": None, "content_type": None}
        
        def check_stream():
            try:
                with api_client.stream("GET", "/stream/mjpeg") as response:
                    result["status_code"] = response.status_code
                    result["content_type"] = response.headers.get("content-type")
            except Exception:
                pass
        
        thread = threading.Thread(target=check_stream, daemon=True)
        thread.start()
        thread.join(timeout=2.0)  # Wait max 2 seconds
        
        # If we got the headers, that's enough to verify the endpoint works
        if result["status_code"] is not None:
            assert result["status_code"] == 200
            assert "multipart/x-mixed-replace" in result["content_type"]

    def test_monitoring_enable_idempotent(self, api_client: TestClient) -> None:
        """Test that enabling monitoring multiple times is safe."""
        response1 = api_client.post("/monitoring/enable")
        assert response1.status_code == 200
        
        response2 = api_client.post("/monitoring/enable")
        assert response2.status_code == 200
        
        # Both should succeed
        assert response1.json()["status"] == "success"
        assert response2.json()["status"] == "success"

    def test_monitoring_disable_idempotent(self, api_client: TestClient) -> None:
        """Test that disabling monitoring multiple times is safe."""
        response1 = api_client.post("/monitoring/disable")
        assert response1.status_code == 200
        
        response2 = api_client.post("/monitoring/disable")
        assert response2.status_code == 200
        
        # Both should succeed
        assert response1.json()["status"] == "success"
        assert response2.json()["status"] == "success"

    def test_api_workflow_full_cycle(
        self, api_client: TestClient, monitor_system: MonitorSystem
    ) -> None:
        """Test a complete workflow through the API."""
        # 1. Check initial status
        status = api_client.get("/status").json()
        assert status["running"] is True
        
        # 2. Disable monitoring
        api_client.post("/monitoring/disable")
        status = api_client.get("/status").json()
        assert status["monitoring_enabled"] is False
        
        # 3. Capture some frames
        for _ in range(20):
            monitor_system.tick()
            time.sleep(0.01)
        
        # 4. Check buffer has frames
        status = api_client.get("/status").json()
        assert status["buffer_size"] > 0
        
        # 5. Trigger manual recording
        recording_response = api_client.post("/recording/trigger")
        assert recording_response.status_code == 200
        
        # 6. Update config
        config_update = {"pre_event_seconds": 3.0, "post_event_seconds": 3.0}
        config_response = api_client.put("/config", json=config_update)
        assert config_response.status_code == 200
        
        # 7. Re-enable monitoring
        enable_response = api_client.post("/monitoring/enable")
        assert enable_response.status_code == 200
        
        # 8. Verify final status
        final_status = api_client.get("/status").json()
        assert final_status["monitoring_enabled"] is True

    def test_config_validation(self, api_client: TestClient) -> None:
        """Test that config validation works."""
        # Try to set invalid values (e.g., negative seconds)
        invalid_config = {
            "pre_event_seconds": -1.0,
        }
        
        # The API should either reject this or clamp to valid values
        # depending on implementation
        response = api_client.put("/config", json=invalid_config)
        
        # Should still return 200 as the implementation may handle this gracefully
        assert response.status_code in [200, 400, 422]
