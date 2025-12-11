from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.monitor_system import MonitorSystem


class ConfigUpdate(BaseModel):
    """Model for configuration updates."""
    pre_event_seconds: Optional[float] = Field(None, ge=0, le=60, description="Seconds to record before event (0-60)")
    post_event_seconds: Optional[float] = Field(None, ge=0, le=60, description="Seconds to record after event (0-60)")
    detection_interval_seconds: Optional[float] = Field(None, gt=0, description="Detection interval in seconds")


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    pre_event_seconds: float
    post_event_seconds: float
    detection_interval_seconds: float
    frame_interval_seconds: float
    enable_monitoring: bool


def create_config_router(monitor: MonitorSystem) -> APIRouter:
    """
    Create router for configuration endpoints.
    
    Args:
        monitor: MonitorSystem instance to control
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/config", tags=["Configuration"])

    @router.get("", response_model=ConfigResponse)
    async def get_config() -> ConfigResponse:
        """
        Get current configuration.
        
        Returns:
            Current system configuration
        """
        config = monitor.config
        return ConfigResponse(
            pre_event_seconds=config.pre_event_seconds,
            post_event_seconds=config.post_event_seconds,
            detection_interval_seconds=config.detection_interval_seconds,
            frame_interval_seconds=config.frame_interval_seconds,
            enable_monitoring=monitor.is_monitoring_enabled()
        )

    @router.put("")
    async def update_config(config_update: ConfigUpdate) -> dict[str, Any]:
        """
        Update system configuration.
        
        Args:
            config_update: Configuration parameters to update
            
        Returns:
            Updated configuration values
        """
        updated_fields = {}
        
        if config_update.pre_event_seconds is not None:
            monitor.config.pre_event_seconds = config_update.pre_event_seconds
            updated_fields["pre_event_seconds"] = config_update.pre_event_seconds
        
        if config_update.post_event_seconds is not None:
            monitor.config.post_event_seconds = config_update.post_event_seconds
            updated_fields["post_event_seconds"] = config_update.post_event_seconds
        
        if config_update.detection_interval_seconds is not None:
            monitor.config.detection_interval_seconds = config_update.detection_interval_seconds
            updated_fields["detection_interval_seconds"] = config_update.detection_interval_seconds
        
        if not updated_fields:
            raise HTTPException(status_code=400, detail="No valid configuration fields provided")
        
        logging.info("Configuration updated: %s", updated_fields)
        return {
            "status": "success",
            "message": "Configuration updated",
            "updated_fields": updated_fields
        }

    return router
