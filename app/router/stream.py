from __future__ import annotations

import logging
from typing import Iterator

import cv2
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.monitor_system import MonitorSystem


def create_stream_router(monitor: MonitorSystem) -> APIRouter:
    """
    Create router for stream endpoints.
    
    Args:
        monitor: MonitorSystem instance to control
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/stream", tags=["Stream"])

    @router.get("/mjpeg")
    async def stream_mjpeg() -> StreamingResponse:
        """
        MJPEG video stream endpoint.
        
        Returns:
            Streaming response with MJPEG video
        """
        if not monitor.is_running():
            raise HTTPException(status_code=503, detail="Camera is not running")

        def generate_mjpeg() -> Iterator[bytes]:
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
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
                        
                    except Exception as e:
                        logging.error("Error generating MJPEG frame: %s", e)
                        break
                        
            except Exception as e:
                logging.error("Error in MJPEG stream: %s", e)

        return StreamingResponse(
            generate_mjpeg(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    return router
