"""Integration tests for MonitorSystem."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from app.monitor_system import MonitorSystem


class TestMonitorSystem:
    """Test cases for MonitorSystem integration."""

    def test_monitor_system_initialization(self, monitor_system: MonitorSystem) -> None:
        """Test that monitor system can be initialized."""
        assert monitor_system is not None
        assert not monitor_system.is_running()
        assert monitor_system.is_monitoring_enabled()

    def test_start_stop_lifecycle(self, monitor_system: MonitorSystem) -> None:
        """Test starting and stopping the monitor system."""
        assert not monitor_system.is_running()
        
        monitor_system.start()
        assert monitor_system.is_running()
        
        monitor_system.stop()
        assert not monitor_system.is_running()

    def test_enable_disable_monitoring(self, monitor_system: MonitorSystem) -> None:
        """Test enabling and disabling monitoring."""
        monitor_system.start()
        
        assert monitor_system.is_monitoring_enabled()
        
        monitor_system.disable_monitoring()
        assert not monitor_system.is_monitoring_enabled()
        
        monitor_system.enable_monitoring()
        assert monitor_system.is_monitoring_enabled()
        
        monitor_system.stop()

    def test_tick_captures_frames(self, monitor_system: MonitorSystem) -> None:
        """Test that tick captures frames into buffer."""
        monitor_system.start()
        
        # Initial buffer should be empty
        assert len(monitor_system.buffer) == 0
        
        # Process a few ticks
        for _ in range(5):
            monitor_system.tick()
        
        # Buffer should have frames
        assert len(monitor_system.buffer) >= 5
        
        monitor_system.stop()

    def test_tick_without_running_does_nothing(self, monitor_system: MonitorSystem) -> None:
        """Test that tick does nothing when system is not running."""
        assert not monitor_system.is_running()
        
        initial_count = len(monitor_system.buffer)
        monitor_system.tick()
        
        # Buffer should not change
        assert len(monitor_system.buffer) == initial_count

    def test_manual_recording_trigger(self, monitor_system: MonitorSystem) -> None:
        """Test manually triggering a recording."""
        monitor_system.start()
        
        # Capture some frames first
        for _ in range(20):
            monitor_system.tick()
            time.sleep(0.01)
        
        # Trigger recording
        output_path = monitor_system.trigger_manual_recording()
        
        assert output_path is not None
        assert Path(output_path).exists()
        assert Path(output_path).suffix == ".mp4"
        
        monitor_system.stop()

    def test_manual_recording_without_running_fails(
        self, monitor_system: MonitorSystem
    ) -> None:
        """Test that manual recording fails when system is not running."""
        assert not monitor_system.is_running()
        
        output_path = monitor_system.trigger_manual_recording()
        assert output_path is None

    def test_get_status(self, monitor_system: MonitorSystem) -> None:
        """Test getting system status."""
        status = monitor_system.get_status()
        
        assert "running" in status
        assert "monitoring_enabled" in status
        assert "is_recording" in status
        assert "buffer_size" in status
        assert "recording_count" in status
        
        assert isinstance(status["running"], bool)
        assert isinstance(status["monitoring_enabled"], bool)
        assert isinstance(status["is_recording"], bool)
        assert isinstance(status["buffer_size"], int)
        assert isinstance(status["recording_count"], int)

    def test_status_reflects_changes(self, monitor_system: MonitorSystem) -> None:
        """Test that status reflects system state changes."""
        status = monitor_system.get_status()
        assert status["running"] is False
        
        monitor_system.start()
        status = monitor_system.get_status()
        assert status["running"] is True
        
        monitor_system.disable_monitoring()
        status = monitor_system.get_status()
        assert status["monitoring_enabled"] is False
        
        monitor_system.stop()
        status = monitor_system.get_status()
        assert status["running"] is False

    def test_recording_lock_prevents_concurrent_recordings(
        self, monitor_system: MonitorSystem
    ) -> None:
        """Test that recording lock prevents concurrent recordings."""
        monitor_system.start()
        
        # Capture some frames
        for _ in range(20):
            monitor_system.tick()
            time.sleep(0.01)
        
        # Simulate concurrent recording attempts
        from threading import Thread
        
        results = []
        
        def trigger_recording() -> None:
            result = monitor_system.trigger_manual_recording()
            results.append(result)
        
        threads = [Thread(target=trigger_recording) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # At least one should succeed, others might be None
        successful = [r for r in results if r is not None]
        assert len(successful) >= 1
        
        monitor_system.stop()

    def test_buffer_size_limited_by_config(self, monitor_system: MonitorSystem) -> None:
        """Test that buffer size is limited by configuration."""
        monitor_system.start()
        
        # Run many ticks (more than buffer capacity)
        for _ in range(150):
            monitor_system.tick()
            time.sleep(0.01)
        
        # Buffer should not grow indefinitely
        buffer_size = len(monitor_system.buffer)
        # Buffer has max_frames=100 in the fixture
        # Buffer should be at or near max capacity but not exceed it
        assert buffer_size <= 100, f"Buffer should be limited by max_frames (got {buffer_size}, expected <=100)"
        # Verify it's actually near capacity (not much smaller)
        assert buffer_size >= 90, f"Buffer should be near capacity (got {buffer_size}, expected >=90)"
        
        monitor_system.stop()

    def test_monitoring_disabled_skips_detection(
        self, monitor_system: MonitorSystem
    ) -> None:
        """Test that disabling monitoring skips detection but still captures frames."""
        monitor_system.start()
        monitor_system.disable_monitoring()
        
        initial_buffer_size = len(monitor_system.buffer)
        
        # Process ticks with monitoring disabled
        for _ in range(10):
            monitor_system.tick()
        
        # Frames should still be captured
        assert len(monitor_system.buffer) > initial_buffer_size
        
        monitor_system.stop()

    def test_multiple_start_stop_cycles(self, monitor_system: MonitorSystem) -> None:
        """Test multiple start/stop cycles."""
        for _ in range(3):
            monitor_system.start()
            assert monitor_system.is_running()
            
            for _ in range(5):
                monitor_system.tick()
            
            monitor_system.stop()
            assert not monitor_system.is_running()

    def test_recording_count_increments(self, monitor_system: MonitorSystem) -> None:
        """Test that recording count increments after each recording."""
        monitor_system.start()
        
        initial_status = monitor_system.get_status()
        initial_count = initial_status["recording_count"]
        
        # Capture frames and record
        for _ in range(20):
            monitor_system.tick()
            time.sleep(0.01)
        
        monitor_system.trigger_manual_recording()
        
        updated_status = monitor_system.get_status()
        assert updated_status["recording_count"] == initial_count + 1
        
        monitor_system.stop()


class TestPresenceDetectorIntegration:
    """Integration tests for PresenceDetector with MonitorSystem."""

    def test_presence_detector_integration(
        self,
        test_config,
        synthetic_camera,
        ring_buffer,
        video_recorder,
        presence_detector
    ) -> None:
        """Test that PresenceDetector integrates correctly with MonitorSystem."""
        from app.monitor_system import MonitorSystem
        
        # Create monitor system with presence detector
        monitor = MonitorSystem(
            config=test_config,
            camera=synthetic_camera,
            buffer=ring_buffer,
            detector=presence_detector,
            recorder=video_recorder,
        )
        
        try:
            monitor.start()
            assert monitor.is_running()
            
            # Run for a few ticks to accumulate frames
            for _ in range(30):
                monitor.tick()
                time.sleep(0.01)
            
            # Verify system is working
            status = monitor.get_status()
            assert status["buffer_size"] > 0
            
        finally:
            if monitor.is_running():
                monitor.stop()
