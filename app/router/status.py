from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.monitor_system import MonitorSystem


class StatusResponse(BaseModel):
    """Response model for system status."""
    running: bool
    monitoring_enabled: bool
    is_recording: bool
    buffer_size: int
    recording_count: int


def create_status_router(monitor: MonitorSystem) -> APIRouter:
    """
    Create router for status endpoints.
    
    Args:
        monitor: MonitorSystem instance to control
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/status", tags=["Status"])

    @router.get("", response_model=StatusResponse)
    async def get_status() -> StatusResponse:
        """
        Get current system status.
        
        Returns:
            System status including monitoring state and buffer information
        """
        status = monitor.get_status()
        return StatusResponse(**status)

    return router
