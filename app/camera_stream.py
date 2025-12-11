from __future__ import annotations

import argparse
import logging
import os
import time
from typing import Any, Iterator, Optional

import cv2
import numpy as np


class CameraStream:
    """Camera stream that supports webcam/RTSP or generates synthetic frames."""

    def __init__(
        self, 
        source: Any = 0, 
        force_synthetic: Optional[bool] = None,
        frame_width: int = 640,
        frame_height: int = 480
    ) -> None:
        """
        Initialize camera stream.
        
        Args:
            source: Camera source (0 for default webcam, RTSP URL string, or video file path)
            force_synthetic: Optionally override hardware usage (True to always use synthetic frames,
                False to always attempt hardware, None to auto-detect)
            frame_width: Target frame width in pixels
            frame_height: Target frame height in pixels
        """
        self.source = source
        self._running = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._use_synthetic = False
        self._frame_count = 0
        self._force_synthetic = force_synthetic
        self.frame_width = frame_width
        self.frame_height = frame_height

    def start(self) -> None:
        """Start the camera stream."""
        if self._running:
            return

        if self._should_use_synthetic():
            logging.info("CameraStream forced to synthetic mode")
            self._use_synthetic = True
            self._running = True
            self._frame_count = 0
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
            Frame data is resized to the configured frame_width x frame_height
            
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
            else:
                # Resize frame from camera to match configured dimensions
                if frame.shape[:2] != (self.frame_height, self.frame_width):
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))
        
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
            Numpy array representing a BGR image with configured dimensions
        """
        # Create a background with animated color using configured dimensions
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        # Calculate animated color based on frame count
        phase = (self._frame_count % 360) * np.pi / 180
        color_r = int(127 + 127 * np.sin(phase))
        color_g = int(127 + 127 * np.sin(phase + 2 * np.pi / 3))
        color_b = int(127 + 127 * np.sin(phase + 4 * np.pi / 3))
        
        frame[:, :] = [color_b, color_g, color_r]
        
        # Add text overlay (scale based on frame height)
        text = f"Synthetic Frame #{self._frame_count}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = self.frame_height / 480.0  # Scale relative to default 480p
        text_thickness = max(1, int(2 * font_scale))
        
        # Center text positions (scaled)
        text_y_center = self.frame_height // 2
        cv2.putText(frame, text, (int(50 * font_scale), text_y_center - int(40 * font_scale)), 
                    font, font_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)
        cv2.putText(frame, "No Camera Available", (int(150 * font_scale), text_y_center), 
                    font, 0.7 * font_scale, (255, 255, 255), max(1, text_thickness - 1), cv2.LINE_AA)
        
        # Add timestamp
        timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp_text, (int(200 * font_scale), text_y_center + int(40 * font_scale)), 
                    font, 0.6 * font_scale, (200, 200, 200), max(1, text_thickness - 1), cv2.LINE_AA)
        
        return frame

    def _should_use_synthetic(self) -> bool:
        """Determine whether synthetic frames should be used without touching hardware."""
        if self._force_synthetic is not None:
            return self._force_synthetic

        if os.environ.get("EDGE_NATIVE_SMART_MONITOR_FORCE_SYNTHETIC") == "1":
            return True

        if os.environ.get("PYTEST_CURRENT_TEST"):
            return True

        return False


def preview_camera_stream(source: Any = 0, duration: Optional[float] = 10.0) -> None:
    """Preview frames from the camera stream in an OpenCV window."""
    camera = CameraStream(source)
    camera.start()
    window_name = "CameraStream Preview"
    start_time = time.time()

    try:
        for frame in camera.frames():
            image = frame["data"]
            cv2.imshow(window_name, image)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break

            if duration is not None and duration > 0:
                if (time.time() - start_time) >= duration:
                    break
    finally:
        camera.stop()
        cv2.destroyWindow(window_name)


def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview frames produced by CameraStream.")
    parser.add_argument(
        "--source",
        default="0",
        help="Camera source (webcam index, RTSP URL, or file path)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Preview duration in seconds (<=0 keeps running until 'q')",
    )
    return parser.parse_args()


def _coerce_source(raw: str) -> Any:
    try:
        return int(raw)
    except ValueError:
        return raw


if __name__ == "__main__":
    args = _parse_cli_args()
    preview_camera_stream(_coerce_source(args.source), args.duration)
