"""Unit tests for Detector module."""

from __future__ import annotations

import numpy as np

from app.detector import Detector, DetectionEvent


class TestDetector:
    """Test cases for Detector."""

    def test_detector_initialization(self) -> None:
        """Test detector can be initialized."""
        detector = Detector()
        assert detector is not None

    def test_should_record_returns_false(self) -> None:
        """Test that default detector always returns False (no-op detector)."""
        detector = Detector()
        
        # Create a test frame
        frame = {
            "timestamp": 1.0,
            "data": np.zeros((480, 640, 3), dtype=np.uint8),
            "frame_number": 1,
        }
        
        result = detector.should_record(frame)
        assert result is False

    def test_should_record_with_multiple_frames(self) -> None:
        """Test that detector consistently returns False for multiple frames."""
        detector = Detector()
        
        for i in range(10):
            frame = {
                "timestamp": i * 0.1,
                "data": np.zeros((480, 640, 3), dtype=np.uint8),
                "frame_number": i + 1,
            }
            result = detector.should_record(frame)
            assert result is False


class TestDetectionEvent:
    """Test cases for DetectionEvent dataclass."""

    def test_detection_event_creation(self) -> None:
        """Test creating a detection event."""
        event = DetectionEvent(
            timestamp=1.0,
            should_record=True,
            frame_number=42,
        )
        
        assert event.timestamp == 1.0
        assert event.should_record is True
        assert event.frame_number == 42
        assert event.details is None

    def test_detection_event_with_details(self) -> None:
        """Test creating a detection event with details."""
        event = DetectionEvent(
            timestamp=1.0,
            should_record=True,
            frame_number=42,
            details={"confidence": 0.95, "object": "person"},
        )
        
        assert event.details == {"confidence": 0.95, "object": "person"}

    def test_detection_event_without_recording(self) -> None:
        """Test creating a detection event that doesn't trigger recording."""
        event = DetectionEvent(
            timestamp=1.0,
            should_record=False,
            frame_number=42,
        )
        
        assert event.should_record is False
