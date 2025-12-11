from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppConfig(BaseModel):
    """Runtime configuration for the monitoring stack."""

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow Path type

    recording_dir: Path = Field(default=Path("recordings"), description="Directory for storing recordings")
    pre_event_seconds: float = Field(default=10.0, ge=0, le=60, description="Seconds to record before event (0-60)")
    post_event_seconds: float = Field(default=10.0, ge=0, le=60, description="Seconds to record after event (0-60)")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring on startup")
    frame_interval_seconds: float = Field(default=0.033, gt=0, description="Frame capture interval (~30 FPS)")
    detection_interval_seconds: float = Field(default=1.0, gt=0, description="Detection interval in seconds")
    camera_source: Any = Field(default=0, description="Camera source (webcam index, RTSP URL, or file path)")
    video_fps: float = Field(default=30.0, gt=0, description="Video FPS for recordings")
    video_codec: str = Field(default="mp4v", min_length=4, max_length=4, description="4-character FourCC codec")
    video_extension: str = Field(default=".mp4", description="Video file extension")
    max_recordings: int = Field(default=50, ge=0, description="Maximum number of recordings to retain")
    frame_width: int = Field(default=640, gt=0, description="Frame width in pixels")
    frame_height: int = Field(default=480, gt=0, description="Frame height in pixels")
    presence_frames_threshold: int = Field(default=3, ge=1, description="Consecutive frames without person to trigger recording")
    presence_cooldown_seconds: float = Field(default=30.0, ge=0, description="Cooldown period after recording before next detection")

    @field_validator('video_extension')
    @classmethod
    def validate_extension(cls, v: str) -> str:
        """Ensure video extension starts with a dot."""
        if not v.startswith('.'):
            return f'.{v}'
        return v

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration and ensure recording directory exists."""
        config = cls()
        config.recording_dir.mkdir(parents=True, exist_ok=True)
        return config
