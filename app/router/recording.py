from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.monitor_system import MonitorSystem


class RecordingResponse(BaseModel):
    """Response model for recording operations."""
    success: bool
    message: str
    file_path: Optional[str] = None


def create_recording_router(monitor: MonitorSystem) -> APIRouter:
    """
    Create router for recording endpoints.
    
    Args:
        monitor: MonitorSystem instance to control
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/recording", tags=["Recording"])

    @router.post("/trigger", response_model=RecordingResponse)
    async def trigger_recording() -> RecordingResponse:
        """
        Manually trigger a recording event.
        
        Returns:
            Recording result with file path if successful
        """
        if not monitor.is_running():
            raise HTTPException(status_code=400, detail="System is not running")
        
        file_path = monitor.trigger_manual_recording()
        
        if file_path:
            return RecordingResponse(
                success=True,
                message="Recording completed successfully",
                file_path=file_path
            )
        else:
            return RecordingResponse(
                success=False,
                message="Recording failed - buffer may be empty or system busy"
            )

    return router
