from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    """Runtime configuration for the monitoring stack."""

    recording_dir: Path = Path("recordings")
    pre_event_seconds: float = 10.0
    post_event_seconds: float = 10.0
    enable_monitoring: bool = True
    frame_interval_seconds: float = 0.033  # ~30 FPS frame capture rate
    detection_interval_seconds: float = 1.0  # Detection runs once per second
    camera_source: Any = 0
    video_fps: float = 30.0
    video_codec: str = "mp4v"
    video_extension: str = ".mp4"
    max_recordings: int = 50

    @classmethod
    def load(cls) -> "AppConfig":
        # Placeholder for real configuration loading logic.
        config = cls()
        config.recording_dir.mkdir(parents=True, exist_ok=True)
        return config
