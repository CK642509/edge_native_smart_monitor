from __future__ import annotations

from collections import deque
from threading import Lock
from time import time
from typing import Any, Deque, Optional


class RingBuffer:
    """Thread-safe buffer that retains frames for a rolling time window."""

    def __init__(self, retention_seconds: float = 10.0, max_frames: Optional[int] = None) -> None:
        """
        Initialize the ring buffer.

        Args:
            retention_seconds (float): Maximum age in seconds for frames to retain. Frames older than this are evicted.
            max_frames (Optional[int]): Optional maximum number of frames to keep. If None, only time-based eviction applies.
        """
        self.retention_seconds = max(0.0, retention_seconds)
        self.max_frames = max_frames if (max_frames is None or max_frames > 0) else None
        
        # Ensure at least one eviction mechanism is active
        if self.retention_seconds <= 0 and self.max_frames is None:
            raise ValueError("Either retention_seconds must be positive or max_frames must be set")
        
        self._frames: Deque[dict[str, Any]] = deque()
        self._lock = Lock()

    def append(self, frame: dict[str, Any]) -> None:
        """
        Append a frame to the buffer and evict old frames if necessary.

        Args:
            frame: A dictionary representing a frame. If the "timestamp" key is missing,
                the current time will be added automatically.

        Notes:
            - If "timestamp" is not provided in the frame, it will be set to the current time.
            - After appending, frames outside the retention window or exceeding max_frames
              will be evicted immediately.
        """
        timestamp = frame.get("timestamp")
        if timestamp is None:
            timestamp = time()
        # Always create a copy of the frame with the correct timestamp
        frame_copy = {**frame, "timestamp": timestamp}

        with self._lock:
            self._frames.append(frame_copy)
            self._evict(timestamp)

    def snapshot(self) -> list[dict[str, Any]]:
        """
        Create a thread-safe snapshot of all frames currently in the buffer.

        Returns:
            A list copy of all frames in chronological order.
        """
        with self._lock:
            return list(self._frames)

    def __len__(self) -> int:
        with self._lock:
            return len(self._frames)

    def _evict(self, now: float) -> None:
        if self.max_frames is not None:
            while len(self._frames) > self.max_frames:
                self._frames.popleft()

        if self.retention_seconds <= 0:
            return

        cutoff = now - self.retention_seconds
        while self._frames and self._frames[0].get("timestamp", 0) < cutoff:
            self._frames.popleft()
