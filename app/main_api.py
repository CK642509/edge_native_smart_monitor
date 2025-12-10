import logging
import sys
import threading
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import uvicorn

from app.api import create_app
from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import Detector
from app.monitor_system import MonitorSystem
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


# Constants
MIN_FRAME_INTERVAL_SECONDS = 1e-3  # 1 millisecond minimum


def run_monitoring_loop(monitor: MonitorSystem) -> None:
    """
    Run the monitoring loop in a separate thread.
    
    Args:
        monitor: MonitorSystem instance to run
    """
    try:
        logging.info("Starting monitoring loop...")
        monitor.run()  # Run indefinitely until stopped
    except Exception as e:
        logging.error("Monitoring loop error: %s", e)


def main() -> None:
    """Main entry point for FastAPI-based monitoring system."""
    # Load configuration and initialize components
    config = AppConfig.load()
    camera = CameraStream(config.camera_source)
    
    # Calculate buffer size based on retention time and frame capture rate
    retention_seconds = max(
        config.pre_event_seconds + config.post_event_seconds,
        1.0,
    )
    frame_interval = max(config.frame_interval_seconds, MIN_FRAME_INTERVAL_SECONDS)
    max_frames = int(retention_seconds / frame_interval) + 1
    
    buffer = RingBuffer(retention_seconds=retention_seconds, max_frames=max_frames)
    detector = Detector()
    recorder = VideoRecorder(
        config.recording_dir,
        fps=config.video_fps,
        codec=config.video_codec,
        file_extension=config.video_extension,
        max_files=config.max_recordings,
    )
    monitor = MonitorSystem(config, camera, buffer, detector, recorder)

    # Start the monitoring system
    monitor.start()
    logging.info("MonitorSystem started")
    
    # Start monitoring loop in a separate thread
    monitor_thread = threading.Thread(
        target=run_monitoring_loop,
        args=(monitor,),
        daemon=True,
        name="MonitoringLoop"
    )
    monitor_thread.start()
    logging.info("Monitoring loop thread started")

    # Create and run FastAPI application
    app = create_app(monitor)
    
    logging.info("=== Edge-Native Smart Monitor API (Step 7) ===")
    logging.info("Starting FastAPI server...")
    logging.info("API documentation: http://127.0.0.1:8000/docs")
    logging.info("MJPEG stream: http://127.0.0.1:8000/stream/mjpeg")
    logging.info("Press Ctrl+C to stop")
    
    try:
        # Run uvicorn server (blocking call)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        # Stop monitoring system
        monitor.stop()
        logging.info("MonitorSystem stopped")


if __name__ == "__main__":
    main()
