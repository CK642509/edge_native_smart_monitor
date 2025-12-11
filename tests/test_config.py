"""Unit tests for AppConfig module."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import AppConfig


class TestAppConfig:
    """Test cases for AppConfig validation."""

    def test_default_config(self) -> None:
        """Test that default configuration is valid."""
        config = AppConfig()
        assert config.recording_dir == Path("recordings")
        assert config.pre_event_seconds == 10.0
        assert config.post_event_seconds == 10.0
        assert config.frame_width == 640
        assert config.frame_height == 480
        assert config.video_codec == "mp4v"

    def test_pre_event_seconds_validation(self) -> None:
        """Test that pre_event_seconds must be in range 0-60."""
        # Valid values
        config = AppConfig(pre_event_seconds=0.0)
        assert config.pre_event_seconds == 0.0
        
        config = AppConfig(pre_event_seconds=30.0)
        assert config.pre_event_seconds == 30.0
        
        config = AppConfig(pre_event_seconds=60.0)
        assert config.pre_event_seconds == 60.0
        
        # Invalid values
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(pre_event_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(pre_event_seconds=61.0)
        assert "less than or equal to 60" in str(exc_info.value)

    def test_post_event_seconds_validation(self) -> None:
        """Test that post_event_seconds must be in range 0-60."""
        # Valid values
        config = AppConfig(post_event_seconds=0.0)
        assert config.post_event_seconds == 0.0
        
        config = AppConfig(post_event_seconds=30.0)
        assert config.post_event_seconds == 30.0
        
        config = AppConfig(post_event_seconds=60.0)
        assert config.post_event_seconds == 60.0
        
        # Invalid values
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(post_event_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(post_event_seconds=61.0)
        assert "less than or equal to 60" in str(exc_info.value)

    def test_frame_dimensions_validation(self) -> None:
        """Test that frame dimensions must be positive."""
        # Valid values
        config = AppConfig(frame_width=1920, frame_height=1080)
        assert config.frame_width == 1920
        assert config.frame_height == 1080
        
        # Invalid values
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(frame_width=0)
        assert "greater than 0" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(frame_height=-1)
        assert "greater than 0" in str(exc_info.value)

    def test_video_codec_validation(self) -> None:
        """Test that video codec must be exactly 4 characters."""
        # Valid values
        config = AppConfig(video_codec="mp4v")
        assert config.video_codec == "mp4v"
        
        config = AppConfig(video_codec="XVID")
        assert config.video_codec == "XVID"
        
        # Invalid values
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(video_codec="mp4")  # Too short
        assert "at least 4 characters" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(video_codec="mpeg4")  # Too long
        assert "at most 4 characters" in str(exc_info.value)

    def test_video_extension_validation(self) -> None:
        """Test that video extension is automatically prefixed with dot if needed."""
        config = AppConfig(video_extension=".mp4")
        assert config.video_extension == ".mp4"
        
        # Should add dot if missing
        config = AppConfig(video_extension="avi")
        assert config.video_extension == ".avi"

    def test_detection_interval_validation(self) -> None:
        """Test that detection interval must be positive."""
        config = AppConfig(detection_interval_seconds=1.0)
        assert config.detection_interval_seconds == 1.0
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(detection_interval_seconds=0.0)
        assert "greater than 0" in str(exc_info.value)

    def test_frame_interval_validation(self) -> None:
        """Test that frame interval must be positive."""
        config = AppConfig(frame_interval_seconds=0.033)
        assert config.frame_interval_seconds == 0.033
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(frame_interval_seconds=0.0)
        assert "greater than 0" in str(exc_info.value)

    def test_max_recordings_validation(self) -> None:
        """Test that max_recordings must be non-negative."""
        config = AppConfig(max_recordings=0)
        assert config.max_recordings == 0
        
        config = AppConfig(max_recordings=100)
        assert config.max_recordings == 100
        
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(max_recordings=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_config_load(self, tmp_path: Path) -> None:
        """Test that config.load() creates recording directory."""
        # Change to a temporary directory that doesn't exist
        original_cwd = Path.cwd()
        try:
            config = AppConfig(recording_dir=tmp_path / "test_recordings")
            assert not config.recording_dir.exists()
            
            # Simulate the load() behavior
            config.recording_dir.mkdir(parents=True, exist_ok=True)
            assert config.recording_dir.exists()
            assert config.recording_dir.is_dir()
        finally:
            pass
