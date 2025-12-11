"""Unit tests for Detector module."""

from __future__ import annotations

import time

import numpy as np

from app.detector import Detector, DetectionEvent, PresenceDetector


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


class TestPresenceDetector:
    """Test cases for PresenceDetector."""
    
    # Test configuration constants
    TEST_MOTION_THRESHOLD = 1000  # Higher than default (500) for more reliable tests

    def test_presence_detector_initialization(self) -> None:
        """Test presence detector can be initialized with default parameters."""
        detector = PresenceDetector()
        assert detector is not None
        assert detector.frames_threshold == 3
        assert detector.cooldown_seconds == 30.0
        assert detector.motion_threshold == 500

    def test_presence_detector_custom_parameters(self) -> None:
        """Test presence detector with custom parameters."""
        detector = PresenceDetector(
            frames_threshold=5,
            cooldown_seconds=60.0,
            motion_threshold=1000
        )
        assert detector.frames_threshold == 5
        assert detector.cooldown_seconds == 60.0
        assert detector.motion_threshold == 1000

    def test_presence_detector_no_trigger_on_first_frame(self) -> None:
        """Test that detector doesn't trigger on first frame."""
        detector = PresenceDetector(frames_threshold=2, cooldown_seconds=0.0)
        
        # Create a frame with no motion (black)
        frame = {
            "timestamp": time.time(),
            "data": np.zeros((480, 640, 3), dtype=np.uint8),
            "frame_number": 1,
        }
        
        result = detector.should_record(frame)
        assert result is False

    def test_presence_detector_trigger_after_threshold(self) -> None:
        """Test that detector triggers after threshold frames without person."""
        # Use higher threshold than default for more reliable testing
        detector = PresenceDetector(
            frames_threshold=2, 
            cooldown_seconds=0.0,
            motion_threshold=self.TEST_MOTION_THRESHOLD
        )
        
        # Skip warmup by manually setting the flag
        detector._warmup_frames = detector._warmup_threshold
        detector._initialized = True
        detector._person_present = True  # Simulate person is present
        
        # Now send frames without motion (person leaves)
        stable_frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        
        # Frame 1 without person - should not trigger yet
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 1,
        }
        # Manually apply to background subtractor first to stabilize it
        for _ in range(5):
            detector.bg_subtractor.apply(stable_frame.copy())
        
        result = detector.should_record(frame_no_motion)
        assert result is False
        assert detector._frames_without_person == 1
        
        # Frame 2 without person - should trigger now (threshold is 2)
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 2,
        }
        result = detector.should_record(frame_no_motion)
        assert result is True

    def test_presence_detector_cooldown(self) -> None:
        """Test that cooldown prevents rapid re-triggering."""
        detector = PresenceDetector(
            frames_threshold=1, 
            cooldown_seconds=1.0,
            motion_threshold=self.TEST_MOTION_THRESHOLD
        )
        
        # Skip warmup
        detector._warmup_frames = detector._warmup_threshold
        detector._initialized = True
        detector._person_present = True
        
        stable_frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        # Stabilize background
        for _ in range(5):
            detector.bg_subtractor.apply(stable_frame.copy())
        
        # Trigger recording (person leaves)
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 1,
        }
        result = detector.should_record(frame_no_motion)
        assert result is True  # First trigger should succeed
        
        # Reset person_present for next test
        detector._person_present = True
        
        # Try to trigger again immediately (during cooldown)
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 2,
        }
        result = detector.should_record(frame_no_motion)
        assert result is False  # Should be blocked by cooldown

    def test_presence_detector_reset_on_motion(self) -> None:
        """Test that motion resets the counter."""
        detector = PresenceDetector(
            frames_threshold=2, 
            cooldown_seconds=0.0,
            motion_threshold=self.TEST_MOTION_THRESHOLD
        )
        
        # Skip warmup
        detector._warmup_frames = detector._warmup_threshold
        detector._initialized = True
        detector._person_present = True
        
        stable_frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        
        # Stabilize background
        for _ in range(5):
            detector.bg_subtractor.apply(stable_frame.copy())
        
        # Start absence (1 frame)
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 1,
        }
        result = detector.should_record(frame_no_motion)
        assert result is False
        assert detector._frames_without_person == 1
        
        # Person returns (simulate by resetting manually)
        detector._person_present = True
        detector._frames_without_person = 0
        
        # Start absence again - need 2 frames to trigger
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 2,
        }
        result = detector.should_record(frame_no_motion)
        assert result is False
        assert detector._frames_without_person == 1
        
        # Second frame should trigger
        frame_no_motion = {
            "timestamp": time.time(),
            "data": stable_frame.copy(),
            "frame_number": 3,
        }
        result = detector.should_record(frame_no_motion)
        assert result is True  # Should trigger after 2 frames

    def test_presence_detector_handles_invalid_frame(self) -> None:
        """Test that detector handles frames without data gracefully."""
        detector = PresenceDetector()
        
        # Frame without data
        frame = {
            "timestamp": time.time(),
            "frame_number": 1,
        }
        result = detector.should_record(frame)
        assert result is False
        
        # Frame with None data
        frame = {
            "timestamp": time.time(),
            "data": None,
            "frame_number": 2,
        }
        result = detector.should_record(frame)
        assert result is False

    def test_presence_detector_is_person_present(self) -> None:
        """Test is_person_present method."""
        detector = PresenceDetector(
            frames_threshold=2,
            cooldown_seconds=0.0,
            motion_threshold=self.TEST_MOTION_THRESHOLD
        )
        
        # Before initialization, should return False
        assert detector.is_person_present() is False
        
        # Skip warmup and initialize
        detector._warmup_frames = detector._warmup_threshold
        detector._initialized = True
        detector._person_present = True
        
        # Now should return True
        assert detector.is_person_present() is True
        
        # When person leaves, should return False
        detector._person_present = False
        assert detector.is_person_present() is False


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
