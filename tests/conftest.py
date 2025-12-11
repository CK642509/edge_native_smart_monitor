"""Shared pytest fixtures for Edge-Native Smart Monitor tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterator

import pytest

from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import Detector
from app.monitor_system import MonitorSystem
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


@pytest.fixture
def temp_recording_dir() -> Iterator[Path]:
    """Create a temporary directory for test recordings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_recording_dir: Path) -> AppConfig:
    """Create a test configuration with temporary recording directory."""
    config = AppConfig(
        recording_dir=temp_recording_dir,
        pre_event_seconds=2.0,
        post_event_seconds=2.0,
        frame_interval_seconds=0.1,  # Faster for tests
        detection_interval_seconds=0.5,  # Faster for tests
        camera_source=0,  # Will use synthetic frames
        video_fps=10.0,
        max_recordings=5,
        frame_width=640,
        frame_height=480
    )
    return config


@pytest.fixture
def synthetic_camera() -> Iterator[CameraStream]:
    """Create a camera stream with synthetic frames for testing."""
    camera = CameraStream(source=0)
    camera.start()
    # Force synthetic mode for tests
    camera._use_synthetic = True
    yield camera
    camera.stop()


@pytest.fixture
def ring_buffer() -> RingBuffer:
    """Create a ring buffer for testing."""
    return RingBuffer(retention_seconds=5.0, max_frames=100)


@pytest.fixture
def video_recorder(temp_recording_dir: Path) -> VideoRecorder:
    """Create a video recorder for testing."""
    return VideoRecorder(
        output_dir=temp_recording_dir,
        fps=10.0,
        codec="mp4v",
        file_extension=".mp4",
        max_files=5,
    )


@pytest.fixture
def detector() -> Detector:
    """Create a detector for testing."""
    return Detector()


@pytest.fixture
def monitor_system(
    test_config: AppConfig,
    synthetic_camera: CameraStream,
    ring_buffer: RingBuffer,
    detector: Detector,
    video_recorder: VideoRecorder,
) -> Iterator[MonitorSystem]:
    """Create a complete monitor system for integration testing."""
    monitor = MonitorSystem(
        config=test_config,
        camera=synthetic_camera,
        buffer=ring_buffer,
        detector=detector,
        recorder=video_recorder,
    )
    yield monitor
    if monitor.is_running():
        monitor.stop()
