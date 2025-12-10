from __future__ import annotations

from fastapi import FastAPI

from app.monitor_system import MonitorSystem
from app.router.config import create_config_router
from app.router.monitoring import create_monitoring_router
from app.router.recording import create_recording_router
from app.router.status import create_status_router
from app.router.stream import create_stream_router


def create_app(monitor: MonitorSystem, lifespan=None) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        monitor: MonitorSystem instance to control
        lifespan: Optional lifespan context manager for startup/shutdown
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Edge-Native Smart Monitor API",
        description="REST API for controlling the smart monitor system",
        version="1.0.0",
        lifespan=lifespan
    )

    @app.get("/", tags=["General"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": "Edge-Native Smart Monitor API",
            "version": "1.0.0",
            "status": "running"
        }

    # Include routers
    app.include_router(create_status_router(monitor))
    app.include_router(create_monitoring_router(monitor))
    app.include_router(create_recording_router(monitor))
    app.include_router(create_config_router(monitor))
    app.include_router(create_stream_router(monitor))

    return app
