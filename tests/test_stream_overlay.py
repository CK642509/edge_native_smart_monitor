"""Tests for stream overlay functionality."""

from __future__ import annotations

import numpy as np
import pytest

from app.router.stream import draw_status_overlay


class TestStreamOverlay:
    """Test cases for stream overlay functionality."""

    def test_draw_status_overlay_with_person_and_recording(
        self,
        monitor_system,
        presence_detector
    ) -> None:
        """Test overlay when person is present and recording."""
        # Setup
        monitor_system.detector = presence_detector
        monitor_system.start()
        
        # Set person present and recording
        presence_detector._initialized = True
        presence_detector._person_present = True
        monitor_system._is_recording = True
        
        # Create a test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw overlay
        result = draw_status_overlay(frame, monitor_system)
        
        # Verify frame was modified
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)  # Should be different
        
        monitor_system.stop()

    def test_draw_status_overlay_without_person(
        self,
        monitor_system,
        presence_detector
    ) -> None:
        """Test overlay when person is not present."""
        # Setup
        monitor_system.detector = presence_detector
        monitor_system.start()
        
        # Set person not present
        presence_detector._initialized = True
        presence_detector._person_present = False
        monitor_system._is_recording = False
        
        # Create a test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw overlay
        result = draw_status_overlay(frame, monitor_system)
        
        # Verify frame was modified
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)  # Should be different
        
        monitor_system.stop()

    def test_draw_status_overlay_does_not_modify_original(
        self,
        monitor_system
    ) -> None:
        """Test that overlay does not modify the original frame."""
        monitor_system.start()
        
        # Create a test frame
        original_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_copy = original_frame.copy()
        
        # Draw overlay
        draw_status_overlay(original_frame, monitor_system)
        
        # Verify original frame was not modified
        assert np.array_equal(original_frame, frame_copy)
        
        monitor_system.stop()
