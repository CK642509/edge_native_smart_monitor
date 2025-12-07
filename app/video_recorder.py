from __future__ import annotations

import logging
from pathlib import Path
from typing import Any


class VideoRecorder:
    """Responsible for writing video clips (placeholder)."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def record_event(self, frames: list[dict[str, Any]]) -> None:
        logging.info("VideoRecorder received %d frames (placeholder)", len(frames))
