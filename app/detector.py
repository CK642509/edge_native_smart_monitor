from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DetectionEvent:
    """Structure representing a detection event."""
    
    timestamp: float
    should_record: bool
    frame_number: Optional[int] = None
    details: Optional[dict[str, Any]] = None


class Detector:
    """Strategy interface for event detection."""

    def should_record(self, frame: dict[str, Any]) -> bool:
        """
        Check if the given frame should trigger a recording.
        
        Args:
            frame: Frame dictionary with 'timestamp', 'data', and 'frame_number' keys
            
        Returns:
            bool: True if recording should be triggered, False otherwise
        """
        return False
