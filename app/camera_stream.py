from __future__ import annotations

import logging
import time
from typing import Any, Iterator, Optional

import cv2
import numpy as np


class CameraStream:
    """Camera stream that supports webcam/RTSP or generates synthetic frames."""

    def __init__(self, source: Any = 0) -> None:
        """
        Initialize camera stream.
        
        Args:
            source: Camera source (0 for default webcam, RTSP URL string, or video file path)
        """
        self.source = source
        self._running = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._use_synthetic = False
        self._frame_count = 0

    def start(self) -> None:
        """Start the camera stream."""
        if self._running:
            return
            
        # Try to open the camera source
        self._cap = cv2.VideoCapture(self.source)
        
        # Check if camera opened successfully
        if not self._cap.isOpened():
            logging.warning(
                "Failed to open camera source '%s', falling back to synthetic frames",
                self.source
            )
            self._use_synthetic = True
            if self._cap is not None:
                self._cap.release()
                self._cap = None
        else:
            logging.info("CameraStream started (source=%s)", self.source)
            self._use_synthetic = False
        
        self._running = True
        self._frame_count = 0

    def stop(self) -> None:
        """Stop the camera stream and release resources."""
        if not self._running:
            return
            
        self._running = False
        
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            
        logging.info("CameraStream stopped")

    def read_frame(self) -> dict[str, Any]:
        """
        Read a single frame from the camera stream.
        
        Returns:
            Dictionary containing 'timestamp', 'data' (numpy array), and 'frame_number'
            
        Raises:
            RuntimeError: If stream is not running
        """
        if not self._running:
            raise RuntimeError("CameraStream is not running")
        
        timestamp = time.time()
        self._frame_count += 1
        
        if self._use_synthetic:
            # Generate synthetic frame
            frame = self._generate_synthetic_frame()
        else:
            # Read from camera
            ret, frame = self._cap.read()
            if not ret:
                logging.warning("Failed to read frame from camera, switching to synthetic frames")
                self._use_synthetic = True
                if self._cap is not None:
                    self._cap.release()
                    self._cap = None
                frame = self._generate_synthetic_frame()
        
        return {
            "timestamp": timestamp,
            "data": frame,
            "frame_number": self._frame_count
        }

    def frames(self) -> Iterator[dict[str, Any]]:
        """
        Iterator that yields frames continuously while the stream is running.
        
        Yields:
            Frame dictionaries from read_frame()
        """
        while self._running:
            try:
                yield self.read_frame()
            except RuntimeError:
                break

    def _generate_synthetic_frame(self) -> np.ndarray:
        """
        Generate a synthetic frame for testing when no camera is available.
        
        Returns:
            Numpy array representing a 640x480 BGR image
        """
        # Create a gradient background
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a color gradient based on frame count
        phase = (self._frame_count % 360) * np.pi / 180
        color_r = int(127 + 127 * np.sin(phase))
        color_g = int(127 + 127 * np.sin(phase + 2 * np.pi / 3))
        color_b = int(127 + 127 * np.sin(phase + 4 * np.pi / 3))
        
        frame[:, :] = [color_b, color_g, color_r]
        
        # Add text overlay
        text = f"Synthetic Frame #{self._frame_count}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, text, (50, 240), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "No Camera Available", (150, 280), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Add timestamp
        timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp_text, (200, 320), font, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
        
        return frame
