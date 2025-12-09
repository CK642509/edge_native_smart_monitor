from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Any, Optional

from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import Detector, DetectionEvent
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


class MonitorSystem:
    """Facade coordinating camera, buffer, detector, and recorder."""

    def __init__(
        self,
        config: AppConfig,
        camera: CameraStream,
        buffer: RingBuffer,
        detector: Detector,
        recorder: VideoRecorder,
    ) -> None:
        self.config = config
        self.camera = camera
        self.buffer = buffer
        self.detector = detector
        self.recorder = recorder
        self._running = False
        self._monitoring_enabled = config.enable_monitoring
        self._last_detection_time = 0.0
        self._is_recording = False
        self._recording_lock = Lock()

    def start(self) -> None:
        """Start the monitoring system (camera and frame capture)."""
        if self._running:
            return
        self.camera.start()
        self._running = True
        self._last_detection_time = time.time()
        logging.info("MonitorSystem started")

    def stop(self) -> None:
        """Stop the monitoring system (camera and frame capture)."""
        if not self._running:
            return
        self.camera.stop()
        self._running = False
        self._is_recording = False
        logging.info("MonitorSystem stopped")
    
    def enable_monitoring(self) -> None:
        """Enable detection and automatic recording without restarting camera."""
        if self._monitoring_enabled:
            logging.debug("Monitoring is already enabled")
            return
        self._monitoring_enabled = True
        # Set to current time minus interval to allow immediate detection on next tick
        self._last_detection_time = time.time() - self.config.detection_interval_seconds
        logging.info("Monitoring enabled")
    
    def disable_monitoring(self) -> None:
        """Disable detection and automatic recording without stopping camera."""
        if not self._monitoring_enabled:
            logging.debug("Monitoring is already disabled")
            return
        self._monitoring_enabled = False
        logging.info("Monitoring disabled")
    
    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring (detection and automatic recording) is enabled."""
        return self._monitoring_enabled
    
    def is_running(self) -> bool:
        """Check if the system is running (camera active)."""
        return self._running
    
    def is_recording(self) -> bool:
        """Check if currently recording an event."""
        return self._is_recording

    def tick(self) -> None:
        """Process one frame: capture, buffer, and optionally detect/record."""
        if not self._running:
            return
        
        # Always capture and buffer the frame
        frame = self.camera.read_frame()
        self.buffer.append(frame)
        
        # Only run detection if monitoring is enabled
        if not self._monitoring_enabled:
            return
        
        # Only run detection at the configured interval
        current_time = time.time()
        if current_time - self._last_detection_time >= self.config.detection_interval_seconds:
            self._last_detection_time = current_time
            
            # Poll detector and create event structure
            should_record = self.detector.should_record(frame)
            event = DetectionEvent(
                timestamp=current_time,
                should_record=should_record,
                frame_number=frame.get("frame_number")
            )
            
            # Output event structure for monitoring
            logging.debug(
                "Detection event: should_record=%s, frame_number=%s, timestamp=%.3f",
                event.should_record,
                event.frame_number,
                event.timestamp
            )
            
            # Trigger recording if needed
            if event.should_record:
                logging.info("Recording triggered by detection event at frame %s", event.frame_number)
                self._trigger_recording()

    def trigger_manual_recording(self) -> Optional[str]:
        """
        Manually trigger a recording event using current buffer contents.
        
        Returns:
            Path to the recorded video file, or None if recording failed
        """
        if not self._running:
            logging.warning("Cannot trigger recording: system is not running")
            return None
        
        logging.info("Manual recording triggered")
        return self._trigger_recording()
    
    def _trigger_recording(self) -> Optional[str]:
        """
        Internal method to trigger recording with pre/post event seconds logic.
        Thread-safe: uses a lock to prevent concurrent recordings.
        
        Returns:
            Path to the recorded video file, or None if recording failed
        """
        # Acquire lock to prevent concurrent recordings
        with self._recording_lock:
            if self._is_recording:
                logging.warning("Recording already in progress, skipping")
                return None
            
            self._is_recording = True
            try:
                # Get all buffered frames
                all_frames = self.buffer.snapshot()
                
                if not all_frames:
                    logging.warning("Cannot record: buffer is empty")
                    return None
                
                # Calculate time window for recording based on pre/post event seconds
                # Use current time as the event time
                event_time = time.time()
                start_time = event_time - self.config.pre_event_seconds
                end_time = event_time + self.config.post_event_seconds
                
                # Filter frames within the time window
                # Validate that frames have valid timestamps
                frames_to_record = [
                    frame for frame in all_frames
                    if "timestamp" in frame 
                    and isinstance(frame["timestamp"], (int, float))
                    and start_time <= frame["timestamp"] <= end_time
                ]
                
                if not frames_to_record:
                    # If no frames match the window, use all available frames
                    logging.debug(
                        "No frames in pre/post window (pre=%.1fs, post=%.1fs), using all %d buffered frames",
                        self.config.pre_event_seconds,
                        self.config.post_event_seconds,
                        len(all_frames)
                    )
                    frames_to_record = all_frames
                else:
                    logging.debug(
                        "Recording %d frames from buffer (pre=%.1fs, post=%.1fs)",
                        len(frames_to_record),
                        self.config.pre_event_seconds,
                        self.config.post_event_seconds
                    )
                
                # Record the filtered frames
                output_path = self.recorder.record_event(frames_to_record)
                return str(output_path) if output_path else None
            finally:
                self._is_recording = False
    
    def get_status(self) -> dict[str, Any]:
        """
        Get current system status.
        
        Returns:
            Dictionary with system status information
        """
        return {
            "running": self._running,
            "monitoring_enabled": self._monitoring_enabled,
            "is_recording": self._is_recording,
            "buffer_size": len(self.buffer),
            "recording_count": self.recorder.get_recording_count(),
        }

    def run(self, runtime_seconds: Optional[float] = None) -> None:
        """
        Main monitoring loop that continuously captures and processes frames.
        
        Args:
            runtime_seconds: Optional duration to run. If None, runs until stopped.
        """
        start_time = time.time()
        try:
            while self._running:
                self.tick()
                if runtime_seconds is not None and time.time() - start_time >= runtime_seconds:
                    break
                time.sleep(self.config.frame_interval_seconds)
        except KeyboardInterrupt:
            logging.info("MonitorSystem interrupted by user")
