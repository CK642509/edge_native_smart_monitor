from __future__ import annotations

from collections import deque
from typing import Any, Deque


class RingBuffer:
    """Simple deque-based buffer for recent frames."""

    def __init__(self, max_frames: int = 60) -> None:
        self._frames: Deque[dict[str, Any]] = deque(maxlen=max_frames)

    def append(self, frame: dict[str, Any]) -> None:
        self._frames.append(frame)

    def snapshot(self) -> list[dict[str, Any]]:
        return list(self._frames)
