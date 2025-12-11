from __future__ import annotations

import logging
from typing import Iterator

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.monitor_system import MonitorSystem


def draw_status_overlay(frame: np.ndarray, monitor: MonitorSystem) -> np.ndarray:
    """
    Draw status overlay on the frame showing person presence and recording status.
    
    Args:
        frame: The frame to draw on
        monitor: MonitorSystem instance to get status from
        
    Returns:
        Frame with overlay drawn
    """
    # Make a copy to avoid modifying the original
    frame_with_overlay = frame.copy()
    
    # Get detector status
    person_present = False
    if hasattr(monitor.detector, 'is_person_present'):
        person_present = monitor.detector.is_person_present()
    
    # Get recording status
    is_recording = monitor.is_recording()
    
    # Position for text (upper left corner with padding)
    x, y = 10, 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    line_spacing = 30
    
    # Draw person presence status
    person_text = "Person: YES" if person_present else "Person: NO"
    person_color = (0, 255, 0) if person_present else (0, 0, 255)  # Green if present, Red if not
    cv2.putText(frame_with_overlay, person_text, (x, y), font, font_scale, (0, 0, 0), thickness + 2)
    cv2.putText(frame_with_overlay, person_text, (x, y), font, font_scale, person_color, thickness)
    
    # Draw recording status
    recording_text = "Recording: YES" if is_recording else "Recording: NO"
    recording_color = (0, 0, 255) if is_recording else (128, 128, 128)  # Red if recording, Gray if not
    cv2.putText(frame_with_overlay, recording_text, (x, y + line_spacing), font, font_scale, (0, 0, 0), thickness + 2)
    cv2.putText(frame_with_overlay, recording_text, (x, y + line_spacing), font, font_scale, recording_color, thickness)
    
    return frame_with_overlay


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
                        
                        # Draw status overlay on the frame
                        frame_with_overlay = draw_status_overlay(frame, monitor)
                        
                        # Encode frame as JPEG
                        ret, buffer = cv2.imencode('.jpg', frame_with_overlay, [cv2.IMWRITE_JPEG_QUALITY, 85])
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
