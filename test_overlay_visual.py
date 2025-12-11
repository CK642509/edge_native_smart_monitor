#!/usr/bin/env python3
"""Visual test to generate a sample frame with overlay."""

import cv2
import numpy as np
from pathlib import Path

from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import PresenceDetector
from app.monitor_system import MonitorSystem
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder
from app.router.stream import draw_status_overlay


def create_sample_frames():
    """Create sample frames showing different states."""
    # Setup minimal monitor system
    config = AppConfig.load()
    camera = CameraStream(source=0, frame_width=640, frame_height=480)
    buffer = RingBuffer(retention_seconds=10.0, max_frames=100)
    detector = PresenceDetector(
        frames_threshold=3,
        cooldown_seconds=30.0
    )
    recorder = VideoRecorder(
        config.recording_dir,
        fps=30.0,
        codec="mp4v",
        file_extension=".mp4",
        max_files=10,
    )
    monitor = MonitorSystem(config, camera, buffer, detector, recorder)
    monitor.start()
    
    # Get a sample frame
    frame = camera.read_frame()['data']
    
    # Create output directory
    output_dir = Path("/tmp/overlay_samples")
    output_dir.mkdir(exist_ok=True)
    
    # State 1: Person present, not recording
    detector._initialized = True
    detector._person_present = True
    monitor._is_recording = False
    frame1 = draw_status_overlay(frame.copy(), monitor)
    cv2.imwrite(str(output_dir / "state1_person_present_not_recording.jpg"), frame1)
    print(f"✓ Saved: {output_dir / 'state1_person_present_not_recording.jpg'}")
    
    # State 2: Person present, recording
    detector._person_present = True
    monitor._is_recording = True
    frame2 = draw_status_overlay(frame.copy(), monitor)
    cv2.imwrite(str(output_dir / "state2_person_present_recording.jpg"), frame2)
    print(f"✓ Saved: {output_dir / 'state2_person_present_recording.jpg'}")
    
    # State 3: No person, not recording
    detector._person_present = False
    monitor._is_recording = False
    frame3 = draw_status_overlay(frame.copy(), monitor)
    cv2.imwrite(str(output_dir / "state3_no_person_not_recording.jpg"), frame3)
    print(f"✓ Saved: {output_dir / 'state3_no_person_not_recording.jpg'}")
    
    # State 4: No person, recording
    detector._person_present = False
    monitor._is_recording = True
    frame4 = draw_status_overlay(frame.copy(), monitor)
    cv2.imwrite(str(output_dir / "state4_no_person_recording.jpg"), frame4)
    print(f"✓ Saved: {output_dir / 'state4_no_person_recording.jpg'}")
    
    monitor.stop()
    
    print(f"\nSample frames saved to: {output_dir}")
    return output_dir


if __name__ == "__main__":
    output_dir = create_sample_frames()
    print(f"\nYou can view the samples at: {output_dir}")
