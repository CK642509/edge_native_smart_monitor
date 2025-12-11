#!/usr/bin/env python3
"""
Demonstration script for PresenceDetector functionality.

This script shows how the PresenceDetector works by:
1. Running for a period with stable synthetic frames (no person)
2. Simulating person presence by changing frames
3. Simulating person leaving by returning to stable frames
4. Showing when recording is triggered
"""

import logging
import time
from pathlib import Path

import numpy as np

from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import PresenceDetector
from app.monitor_system import MonitorSystem
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


logging.basicConfig(
    level=logging.INFO, 
    format="[%(asctime)s] %(levelname)s: %(message)s"
)


class DemoCamera(CameraStream):
    """Custom camera that simulates person entering and leaving."""
    
    def __init__(self):
        super().__init__(source=0, frame_width=640, frame_height=480)
        self._demo_frame_count = 0
        self._use_synthetic = True  # Force synthetic mode
        
    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generate synthetic frame with person simulation."""
        self._demo_frame_count += 1
        
        # Create base frame (gray background)
        frame = np.ones((self.frame_height, self.frame_width, 3), dtype=np.uint8) * 50
        
        # Frames 20-60: Person present (bright rectangle simulating person)
        if 20 <= self._demo_frame_count <= 60:
            frame[100:350, 200:440, :] = 200  # Bright area representing person
            
        return frame


def main():
    """Run presence detector demonstration."""
    print("=" * 70)
    print("PresenceDetector Demonstration")
    print("=" * 70)
    print("\nThis demo simulates a person entering and leaving the frame:")
    print("  - Frames 1-19:   No person (stable background)")
    print("  - Frames 20-60:  Person present (motion detected)")
    print("  - Frames 61+:    Person leaves (stable background returns)")
    print("\nThe detector should trigger recording a few frames after the person leaves.")
    print("=" * 70)
    print()
    
    # Configure for demo
    config = AppConfig(
        recording_dir=Path("demo_recordings"),
        pre_event_seconds=2.0,  # Record 2 seconds before
        post_event_seconds=2.0,  # Record 2 seconds after
        frame_interval_seconds=0.1,  # 10 FPS
        detection_interval_seconds=0.1,  # Check every frame
        presence_frames_threshold=3,  # Trigger after 3 frames without person
        presence_cooldown_seconds=5.0,  # 5 second cooldown
        max_recordings=10,
    )
    config.recording_dir.mkdir(exist_ok=True)
    
    # Create components
    camera = DemoCamera()
    buffer = RingBuffer(retention_seconds=10.0, max_frames=200)
    detector = PresenceDetector(
        frames_threshold=config.presence_frames_threshold,
        cooldown_seconds=config.presence_cooldown_seconds,
        motion_threshold=5000  # Tuned for demo
    )
    recorder = VideoRecorder(
        config.recording_dir,
        fps=10.0,
        codec="mp4v",
        file_extension=".mp4",
        max_files=config.max_recordings,
    )
    monitor = MonitorSystem(config, camera, buffer, detector, recorder)
    
    # Run demonstration
    try:
        monitor.start()
        logging.info("Started monitoring...")
        
        # Run for 10 seconds (100 frames at 10 FPS)
        for i in range(100):
            monitor.tick()
            time.sleep(0.1)
            
            # Log key events
            if i == 19:
                logging.info(">>> Person entering frame...")
            elif i == 60:
                logging.info(">>> Person leaving frame...")
        
        status = monitor.get_status()
        logging.info("\n" + "=" * 70)
        logging.info("Demo complete!")
        logging.info(f"  Total frames captured: {status['buffer_size']}")
        logging.info(f"  Recordings created: {status['recording_count']}")
        
        if status['recording_count'] > 0:
            logging.info(f"\nRecordings saved to: {config.recording_dir}/")
            for video in sorted(config.recording_dir.glob("*.mp4")):
                size_kb = video.stat().st_size / 1024
                logging.info(f"  - {video.name} ({size_kb:.1f} KB)")
        else:
            logging.info("\nNo recordings were triggered (detector may need tuning)")
        
        logging.info("=" * 70)
        
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
