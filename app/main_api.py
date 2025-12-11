import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import uvicorn
from fastapi import FastAPI

from app.api import create_app
from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import PresenceDetector
from app.monitor_system import MonitorSystem
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


# Constants
MIN_FRAME_INTERVAL_SECONDS = 1e-3  # 1 millisecond minimum


async def run_monitoring_loop(monitor: MonitorSystem) -> None:
    """
    Run the monitoring loop asynchronously.
    
    Args:
        monitor: MonitorSystem instance to run
    """
    try:
        logging.info("Starting monitoring loop...")
        loop = asyncio.get_running_loop()
        while monitor.is_running():
            # Run tick in executor to avoid blocking event loop
            await loop.run_in_executor(None, monitor.tick)
            await asyncio.sleep(monitor.config.frame_interval_seconds)
    except asyncio.CancelledError:
        logging.info("Monitoring loop cancelled")
        raise
    except Exception as e:
        logging.error("Monitoring loop error: %s", e)


def main() -> None:
    """Main entry point for FastAPI-based monitoring system."""
    # Load configuration and initialize components
    config = AppConfig.load()
    camera = CameraStream(
        config.camera_source,
        frame_width=config.frame_width,
        frame_height=config.frame_height
    )
    
    # Calculate buffer size based on retention time and frame capture rate
    retention_seconds = max(
        config.pre_event_seconds + config.post_event_seconds,
        1.0,
    )
    frame_interval = max(config.frame_interval_seconds, MIN_FRAME_INTERVAL_SECONDS)
    max_frames = int(retention_seconds / frame_interval) + 1
    
    buffer = RingBuffer(retention_seconds=retention_seconds, max_frames=max_frames)
    detector = PresenceDetector(
        frames_threshold=config.presence_frames_threshold,
        cooldown_seconds=config.presence_cooldown_seconds
    )
    recorder = VideoRecorder(
        config.recording_dir,
        fps=config.video_fps,
        codec=config.video_codec,
        file_extension=config.video_extension,
        max_files=config.max_recordings,
    )
    monitor = MonitorSystem(config, camera, buffer, detector, recorder)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """
        FastAPI lifespan context manager for startup and shutdown.
        
        Args:
            app: FastAPI application instance
        """
        # Startup
        monitor.start()
        logging.info("MonitorSystem started")
        
        # Start monitoring loop as background task
        monitoring_task = asyncio.create_task(run_monitoring_loop(monitor))
        logging.info("Monitoring loop task started")
        
        logging.info("=== Edge-Native Smart Monitor API (Step 7) ===")
        logging.info("API documentation: http://127.0.0.1:8000/docs")
        logging.info("MJPEG stream: http://127.0.0.1:8000/stream/mjpeg")
        
        yield
        
        # Shutdown
        logging.info("Shutting down...")
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        monitor.stop()
        logging.info("MonitorSystem stopped")

    # Create FastAPI application with lifespan
    app = create_app(monitor, lifespan=lifespan)
    
    logging.info("Starting FastAPI server...")
    logging.info("Press Ctrl+C to stop")
    
    # Run uvicorn server (blocking call)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
