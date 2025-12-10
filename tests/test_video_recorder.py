"""Unit tests for VideoRecorder module."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.video_recorder import VideoRecorder


class TestVideoRecorder:
    """Test cases for VideoRecorder."""

    def test_recorder_initialization(self, temp_recording_dir: Path) -> None:
        """Test video recorder can be initialized."""
        recorder = VideoRecorder(
            output_dir=temp_recording_dir,
            fps=10.0,
            codec="mp4v",
            file_extension=".mp4",
            max_files=5,
        )
        assert recorder.output_dir == temp_recording_dir
        assert recorder.fps == 10.0
        assert recorder.codec == "mp4v"
        assert recorder.file_extension == ".mp4"
        assert recorder.max_files == 5
        assert temp_recording_dir.exists()

    def test_invalid_codec_length(self, temp_recording_dir: Path) -> None:
        """Test that invalid codec length raises error."""
        with pytest.raises(ValueError, match="Codec must be exactly 4 characters"):
            VideoRecorder(
                output_dir=temp_recording_dir,
                fps=10.0,
                codec="invalid",  # 7 characters, exceeds required 4-character limit
                file_extension=".mp4",
            )

    def test_record_event_creates_file(self, video_recorder: VideoRecorder) -> None:
        """Test that recording an event creates a video file."""
        # Create test frames
        frames = []
        for i in range(10):
            frame = {
                "timestamp": i * 0.1,
                "data": np.zeros((480, 640, 3), dtype=np.uint8),
                "frame_number": i + 1,
            }
            frames.append(frame)
        
        output_path = video_recorder.record_event(frames)
        
        assert output_path is not None
        output_file = Path(output_path)
        assert output_file.exists()
        assert output_file.suffix == ".mp4"
        assert output_file.stat().st_size > 0

    def test_record_event_with_empty_frames(self, video_recorder: VideoRecorder) -> None:
        """Test that recording with empty frame list returns None."""
        output_path = video_recorder.record_event([])
        assert output_path is None

    def test_filename_includes_timestamp(self, video_recorder: VideoRecorder) -> None:
        """Test that generated filenames include timestamp with milliseconds."""
        frames = [
            {"timestamp": 1.0, "data": np.zeros((480, 640, 3), dtype=np.uint8)}
        ]
        
        output_path = video_recorder.record_event(frames)
        assert output_path is not None
        
        filename = Path(output_path).name
        assert filename.startswith("event_")
        assert filename.endswith(".mp4")
        # Should have format: event_YYYYMMDD_HHMMSS_mmm.mp4
        parts = filename.split("_")
        assert len(parts) >= 4

    def test_retention_policy_deletes_old_files(
        self, temp_recording_dir: Path
    ) -> None:
        """Test that retention policy deletes old files when max_files is exceeded."""
        recorder = VideoRecorder(
            output_dir=temp_recording_dir,
            fps=10.0,
            codec="mp4v",
            file_extension=".mp4",
            max_files=3,
        )
        
        frames = [{"data": np.zeros((480, 640, 3), dtype=np.uint8)}]
        
        # Record 5 events
        for _ in range(5):
            recorder.record_event(frames)
        
        # Should only keep 3 most recent files
        assert recorder.get_recording_count() == 3

    def test_max_files_none_unlimited(self, temp_recording_dir: Path) -> None:
        """Test that max_files=None allows unlimited files."""
        recorder = VideoRecorder(
            output_dir=temp_recording_dir,
            fps=10.0,
            codec="mp4v",
            file_extension=".mp4",
            max_files=None,
        )
        
        frames = [{"data": np.zeros((480, 640, 3), dtype=np.uint8)}]
        
        # Record 5 events
        for _ in range(5):
            recorder.record_event(frames)
        
        # All files should be kept
        assert recorder.get_recording_count() == 5

    def test_max_files_zero_deletes_all(self, temp_recording_dir: Path) -> None:
        """Test that max_files=0 deletes all files immediately."""
        recorder = VideoRecorder(
            output_dir=temp_recording_dir,
            fps=10.0,
            codec="mp4v",
            file_extension=".mp4",
            max_files=0,
        )
        
        frames = [{"data": np.zeros((480, 640, 3), dtype=np.uint8)}]
        recorder.record_event(frames)
        
        # No files should remain
        assert recorder.get_recording_count() == 0

    def test_record_event_with_mismatched_dimensions(
        self, video_recorder: VideoRecorder
    ) -> None:
        """Test that frames with mismatched dimensions are skipped."""
        frames = [
            {"data": np.zeros((480, 640, 3), dtype=np.uint8), "frame_number": 1},
            {"data": np.zeros((240, 320, 3), dtype=np.uint8), "frame_number": 2},  # Wrong size
            {"data": np.zeros((480, 640, 3), dtype=np.uint8), "frame_number": 3},
        ]
        
        output_path = video_recorder.record_event(frames)
        
        # Should still create a file with valid frames
        assert output_path is not None
        assert Path(output_path).exists()

    def test_record_event_with_invalid_first_frame(
        self, video_recorder: VideoRecorder
    ) -> None:
        """Test that recording fails gracefully with invalid first frame."""
        frames = [
            {"data": None},  # Invalid first frame
        ]
        
        output_path = video_recorder.record_event(frames)
        assert output_path is None

    def test_get_recording_count(self, video_recorder: VideoRecorder) -> None:
        """Test getting the count of recorded files."""
        assert video_recorder.get_recording_count() == 0
        
        frames = [{"data": np.zeros((480, 640, 3), dtype=np.uint8)}]
        video_recorder.record_event(frames)
        
        assert video_recorder.get_recording_count() == 1
        
        video_recorder.record_event(frames)
        assert video_recorder.get_recording_count() == 2

    def test_record_multiple_frames_with_content(
        self, video_recorder: VideoRecorder
    ) -> None:
        """Test recording multiple frames with different content."""
        frames = []
        for i in range(30):
            # Create frame with gradient for visual verification
            frame_data = np.ones((480, 640, 3), dtype=np.uint8) * (i * 8)
            frame = {
                "timestamp": i * 0.033,
                "data": frame_data,
                "frame_number": i + 1,
            }
            frames.append(frame)
        
        output_path = video_recorder.record_event(frames)
        
        assert output_path is not None
        output_file = Path(output_path)
        assert output_file.exists()
        # File should be larger with more frames
        assert output_file.stat().st_size > 10000
