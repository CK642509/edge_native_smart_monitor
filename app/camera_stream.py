from __future__ import annotations

import logging
import time
from typing import Any


class CameraStream:
    """Placeholder camera stream that emits dummy frames."""

    def __init__(self, source: Any = 0) -> None:
        self.source = source
        self._running = False

    def start(self) -> None:
        logging.info("CameraStream started (source=%s)", self.source)
        self._running = True

    def stop(self) -> None:
        logging.info("CameraStream stopped")
        self._running = False

    def read_frame(self) -> dict[str, Any]:
        if not self._running:
            raise RuntimeError("CameraStream is not running")
        return {"timestamp": time.time(), "data": None}
