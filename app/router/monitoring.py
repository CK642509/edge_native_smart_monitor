from __future__ import annotations

from fastapi import APIRouter

from app.monitor_system import MonitorSystem


def create_monitoring_router(monitor: MonitorSystem) -> APIRouter:
    """
    Create router for monitoring control endpoints.
    
    Args:
        monitor: MonitorSystem instance to control
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

    @router.post("/enable")
    async def enable_monitoring() -> dict[str, str]:
        """
        Enable monitoring (detection and automatic recording).
        
        Returns:
            Success message
        """
        monitor.enable_monitoring()
        return {"status": "success", "message": "Monitoring enabled"}

    @router.post("/disable")
    async def disable_monitoring() -> dict[str, str]:
        """
        Disable monitoring (detection and automatic recording).
        Camera continues capturing frames.
        
        Returns:
            Success message
        """
        monitor.disable_monitoring()
        return {"status": "success", "message": "Monitoring disabled"}

    return router
