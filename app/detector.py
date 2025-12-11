from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import cv2
import numpy as np


@dataclass
class DetectionEvent:
    """Structure representing a detection event."""
    
    timestamp: float
    should_record: bool
    frame_number: Optional[int] = None
    details: Optional[dict[str, Any]] = None


class Detector:
    """Strategy interface for event detection."""

    def should_record(self, frame: dict[str, Any]) -> bool:
        """
        Check if the given frame should trigger a recording.
        
        Args:
            frame: Frame dictionary with 'timestamp', 'data', and 'frame_number' keys
            
        Returns:
            bool: True if recording should be triggered, False otherwise
        """
        return False


class PresenceDetector(Detector):
    """
    Detector that triggers recording when a person leaves the frame.
    
    Uses background subtraction to detect motion/presence in the frame.
    When a person leaves (consecutive frames with no significant motion),
    it triggers a recording event.
    """
    
    # Default configuration constants
    DEFAULT_BG_HISTORY = 100  # Number of frames for background model
    DEFAULT_BG_VAR_THRESHOLD = 25  # Variance threshold for background/foreground separation
    DEFAULT_WARMUP_FRAMES = 10  # Number of frames needed to initialize background model
    
    def __init__(
        self,
        frames_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        motion_threshold: int = 500,
    ) -> None:
        """
        Initialize the presence detector.
        
        Args:
            frames_threshold: Number of consecutive frames without person to trigger recording
            cooldown_seconds: Cooldown period after recording before next detection
            motion_threshold: Minimum number of motion pixels to consider person present
        """
        self.frames_threshold = frames_threshold
        self.cooldown_seconds = cooldown_seconds
        self.motion_threshold = motion_threshold
        
        # Background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=self.DEFAULT_BG_HISTORY,
            varThreshold=self.DEFAULT_BG_VAR_THRESHOLD,
            detectShadows=False
        )
        
        # State tracking
        self._person_present = False
        self._frames_without_person = 0
        self._last_recording_time = 0.0
        self._initialized = False
        self._warmup_frames = 0
        self._warmup_threshold = self.DEFAULT_WARMUP_FRAMES
    
    def should_record(self, frame: dict[str, Any]) -> bool:
        """
        Check if recording should be triggered based on person leaving the frame.
        
        Args:
            frame: Frame dictionary with 'timestamp', 'data', and 'frame_number' keys
            
        Returns:
            bool: True if person just left (after consecutive frames without person), False otherwise
        """
        # Check cooldown period
        current_time = time.time()
        if current_time - self._last_recording_time < self.cooldown_seconds:
            return False
        
        # Extract frame data
        frame_data = frame.get("data")
        if frame_data is None or not isinstance(frame_data, np.ndarray):
            return False
        
        # Warm up the background subtractor
        if self._warmup_frames < self._warmup_threshold:
            self.bg_subtractor.apply(frame_data)
            self._warmup_frames += 1
            return False
        
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame_data)
        
        # Count non-zero pixels (motion detection)
        motion_pixels = cv2.countNonZero(fg_mask)
        
        # Determine if person is present based on motion threshold
        person_detected = motion_pixels > self.motion_threshold
        
        # Initialize state on first detection after warmup
        if not self._initialized:
            self._person_present = person_detected
            self._initialized = True
            return False
        
        # Track state changes
        if person_detected:
            # Person is present - reset counter
            self._person_present = True
            self._frames_without_person = 0
            return False
        else:
            # No person detected
            if self._person_present:
                # Person was present before, increment counter
                self._frames_without_person += 1
                
                # Check if threshold reached (person has left)
                if self._frames_without_person >= self.frames_threshold:
                    # Person has left - trigger recording
                    self._person_present = False
                    self._frames_without_person = 0
                    self._last_recording_time = current_time
                    return True
            else:
                # Person was already absent
                self._frames_without_person = 0
            
            return False
