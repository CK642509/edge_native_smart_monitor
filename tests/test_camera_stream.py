"""Unit tests for CameraStream module."""

from __future__ import annotations

import numpy as np
import pytest

from app.camera_stream import CameraStream


class TestCameraStream:
    """Test cases for CameraStream with synthetic frames."""

    def test_camera_start_stop(self) -> None:
        """Test camera can start and stop properly."""
        camera = CameraStream(source=0)
        assert not camera._running
        
        camera.start()
        assert camera._running
        # Should use synthetic frames in test environment
        assert camera._use_synthetic
        
        camera.stop()
        assert not camera._running

    def test_synthetic_frame_generation(self) -> None:
        """Test synthetic frame generation produces valid frames."""
        camera = CameraStream(source=0)
        camera.start()
        camera._use_synthetic = True
        
        frame = camera.read_frame()
        
        assert "timestamp" in frame
        assert "data" in frame
        assert "frame_number" in frame
        assert isinstance(frame["timestamp"], float)
        assert isinstance(frame["data"], np.ndarray)
        assert frame["data"].shape == (480, 640, 3)
        assert frame["frame_number"] == 1
        
        camera.stop()

    def test_read_frame_requires_running(self) -> None:
        """Test that read_frame raises error when camera is not running."""
        camera = CameraStream(source=0)
        
        with pytest.raises(RuntimeError, match="CameraStream is not running"):
            camera.read_frame()

    def test_frame_iterator(self) -> None:
        """Test frame iterator yields multiple frames."""
        camera = CameraStream(source=0)
        camera.start()
        camera._use_synthetic = True
        
        frame_count = 0
        for frame in camera.frames():
            frame_count += 1
            assert "data" in frame
            assert isinstance(frame["data"], np.ndarray)
            if frame_count >= 5:
                break
        
        assert frame_count == 5
        camera.stop()

    def test_frame_numbers_increment(self) -> None:
        """Test that frame numbers increment correctly."""
        camera = CameraStream(source=0)
        camera.start()
        camera._use_synthetic = True
        
        frame1 = camera.read_frame()
        frame2 = camera.read_frame()
        frame3 = camera.read_frame()
        
        assert frame1["frame_number"] == 1
        assert frame2["frame_number"] == 2
        assert frame3["frame_number"] == 3
        
        camera.stop()

    def test_multiple_start_calls_are_safe(self) -> None:
        """Test that calling start multiple times doesn't cause issues."""
        camera = CameraStream(source=0)
        
        camera.start()
        assert camera._running
        
        camera.start()  # Second call should be safe
        assert camera._running
        
        camera.stop()

    def test_multiple_stop_calls_are_safe(self) -> None:
        """Test that calling stop multiple times doesn't cause issues."""
        camera = CameraStream(source=0)
        camera.start()
        
        camera.stop()
        assert not camera._running
        
        camera.stop()  # Second call should be safe
        assert not camera._running

    def test_synthetic_frames_have_different_colors(self) -> None:
        """Test that synthetic frames have animated colors."""
        camera = CameraStream(source=0)
        camera.start()
        camera._use_synthetic = True
        
        frame1 = camera.read_frame()
        frame2 = camera.read_frame()
        
        # Colors should be different due to animation
        color1 = frame1["data"][0, 0].tolist()
        color2 = frame2["data"][0, 0].tolist()
        assert color1 != color2, "Animated frames should have different colors"
        
        camera.stop()
