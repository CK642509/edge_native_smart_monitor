from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np


class VideoRecorder:
    """Responsible for writing video clips to disk."""

    def __init__(
        self,
        output_dir: Path,
        fps: float = 30.0,
        codec: str = "mp4v",
        file_extension: str = ".mp4",
        max_files: Optional[int] = None,
    ) -> None:
        """
        Initialize the video recorder.

        Args:
            output_dir: Directory where video files will be saved
            fps: Frames per second for output video
            codec: FourCC codec string (e.g., 'mp4v', 'XVID', 'MJPG')
            file_extension: File extension for output files (e.g., '.mp4', '.avi')
            max_files: Maximum number of video files to retain. Older files are deleted when exceeded.
        """
        self.output_dir = output_dir
        self.fps = fps
        self.codec = codec
        self.file_extension = file_extension
        self.max_files = max_files
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(
            "VideoRecorder initialized (dir=%s, fps=%.1f, codec=%s, ext=%s, max_files=%s)",
            self.output_dir, self.fps, self.codec, self.file_extension, self.max_files
        )

    def record_event(self, frames: list[dict[str, Any]]) -> Optional[Path]:
        """
        Write frames to a video file on disk.

        Args:
            frames: List of frame dictionaries, each containing 'data' (numpy array) and 'timestamp'

        Returns:
            Path to the created video file, or None if recording failed
        """
        if not frames:
            logging.warning("VideoRecorder received empty frame list, skipping recording")
            return None

        # Generate filename with timestamp (including milliseconds for uniqueness)
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        milliseconds = now.microsecond // 1000
        filename = f"event_{timestamp}_{milliseconds:03d}{self.file_extension}"
        output_path = self.output_dir / filename

        try:
            # Get frame dimensions from first frame
            first_frame = frames[0]["data"]
            if not isinstance(first_frame, np.ndarray):
                logging.error("Frame data is not a numpy array")
                return None

            height, width = first_frame.shape[:2]
            
            # Create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            writer = cv2.VideoWriter(
                str(output_path),
                fourcc,
                self.fps,
                (width, height)
            )

            if not writer.isOpened():
                logging.error("Failed to open VideoWriter for %s", output_path)
                return None

            # Write all frames
            frames_written = 0
            for frame in frames:
                frame_data = frame.get("data")
                if frame_data is not None and isinstance(frame_data, np.ndarray):
                    writer.write(frame_data)
                    frames_written += 1

            writer.release()

            logging.info(
                "VideoRecorder saved %d frames to %s (%.2f MB)",
                frames_written,
                output_path,
                output_path.stat().st_size / (1024 * 1024)
            )

            # Apply retention policy
            self._apply_retention_policy()

            return output_path

        except Exception as e:
            logging.error("Failed to record video: %s", e, exc_info=True)
            # Clean up partial file if it exists
            if output_path.exists():
                output_path.unlink()
            return None

    def _apply_retention_policy(self) -> None:
        """
        Apply retention policy by deleting oldest video files if max_files is exceeded.
        """
        if self.max_files is None or self.max_files <= 0:
            return

        # Get all video files in the output directory
        video_files = sorted(
            self.output_dir.glob(f"*{self.file_extension}"),
            key=lambda p: p.stat().st_mtime
        )

        # Delete oldest files if we exceed max_files
        files_to_delete = len(video_files) - self.max_files
        if files_to_delete > 0:
            for file_path in video_files[:files_to_delete]:
                try:
                    file_path.unlink()
                    logging.info("Deleted old recording: %s", file_path.name)
                except Exception as e:
                    logging.error("Failed to delete %s: %s", file_path, e)

    def get_recording_count(self) -> int:
        """
        Get the number of video files currently stored.

        Returns:
            Number of video files in the output directory
        """
        return len(list(self.output_dir.glob(f"*{self.file_extension}")))
