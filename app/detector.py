from __future__ import annotations

from typing import Any


class Detector:
    """Strategy interface for event detection."""

    def should_record(self, frame: dict[str, Any]) -> bool:
        return False
