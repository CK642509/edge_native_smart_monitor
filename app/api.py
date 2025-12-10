from __future__ import annotations

import logging
from typing import Any, Optional

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.monitor_system import MonitorSystem


class ConfigUpdate(BaseModel):
    """Model for configuration updates."""
    pre_event_seconds: Optional[float] = Field(None, ge=0, description="Seconds to record before event")
    post_event_seconds: Optional[float] = Field(None, ge=0, description="Seconds to record after event")
    detection_interval_seconds: Optional[float] = Field(None, gt=0, description="Detection interval in seconds")


class RecordingResponse(BaseModel):
    """Response model for recording operations."""
    success: bool
    message: str
    file_path: Optional[str] = None


class StatusResponse(BaseModel):
    """Response model for system status."""
    running: bool
    monitoring_enabled: bool
    is_recording: bool
    buffer_size: int
    recording_count: int


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    pre_event_seconds: float
    post_event_seconds: float
    detection_interval_seconds: float
    frame_interval_seconds: float
    enable_monitoring: bool


def create_app(monitor: MonitorSystem) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        monitor: MonitorSystem instance to control
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Edge-Native Smart Monitor API",
        description="REST API for controlling the smart monitor system",
        version="1.0.0"
    )

    @app.get("/", tags=["General"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": "Edge-Native Smart Monitor API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/status", response_model=StatusResponse, tags=["Status"])
    async def get_status() -> StatusResponse:
        """
        Get current system status.
        
        Returns:
            System status including monitoring state and buffer information
        """
        status = monitor.get_status()
        return StatusResponse(**status)

    @app.post("/monitoring/enable", tags=["Monitoring"])
    async def enable_monitoring() -> dict[str, str]:
        """
        Enable monitoring (detection and automatic recording).
        
        Returns:
            Success message
        """
        monitor.enable_monitoring()
        return {"status": "success", "message": "Monitoring enabled"}

    @app.post("/monitoring/disable", tags=["Monitoring"])
    async def disable_monitoring() -> dict[str, str]:
        """
        Disable monitoring (detection and automatic recording).
        Camera continues capturing frames.
        
        Returns:
            Success message
        """
        monitor.disable_monitoring()
        return {"status": "success", "message": "Monitoring disabled"}

    @app.post("/recording/trigger", response_model=RecordingResponse, tags=["Recording"])
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

    @app.get("/config", response_model=ConfigResponse, tags=["Configuration"])
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

    @app.put("/config", tags=["Configuration"])
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

    @app.get("/stream/mjpeg", tags=["Stream"])
    async def stream_mjpeg() -> StreamingResponse:
        """
        MJPEG video stream endpoint.
        
        Returns:
            Streaming response with MJPEG video
        """
        if not monitor.is_running():
            raise HTTPException(status_code=503, detail="Camera is not running")

        def generate_mjpeg() -> bytes:
            """Generate MJPEG stream from camera frames."""
            try:
                while monitor.is_running():
                    try:
                        # Read current frame from camera
                        frame_dict = monitor.camera.read_frame()
                        frame = frame_dict.get("data")
                        
                        if frame is None:
                            continue
                        
                        # Encode frame as JPEG
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if not ret:
                            continue
                        
                        # Yield frame in MJPEG format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               buffer.tobytes() + b'\r\n')
                        
                    except Exception as e:
                        logging.error("Error generating MJPEG frame: %s", e)
                        break
                        
            except Exception as e:
                logging.error("Error in MJPEG stream: %s", e)

        return StreamingResponse(
            generate_mjpeg(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    return app
