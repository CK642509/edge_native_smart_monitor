import logging
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import Detector
from app.monitor_system import MonitorSystem
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


# Constants
MIN_FRAME_INTERVAL_SECONDS = 1e-3  # 1 millisecond minimum


def main() -> None:
    config = AppConfig.load()
    camera = CameraStream(config.camera_source)
    
    # Calculate buffer size based on retention time and frame capture rate
    retention_seconds = max(
        config.pre_event_seconds + config.post_event_seconds,
        1.0,
    )
    frame_interval = max(config.frame_interval_seconds, MIN_FRAME_INTERVAL_SECONDS)
    # Calculate max_frames based on actual frame capture rate to store all frames
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

    # Demonstrate Step 6: Monitoring Coordination Layer
    logging.info("=== Demonstrating MonitorSystem Capabilities (Step 6) ===")
    
    # Start the system
    monitor.start()
    status = monitor.get_status()
    logging.info(
        "System started - running=%s, monitoring=%s, buffer_size=%d",
        status["running"], status["monitoring_enabled"], status["buffer_size"]
    )
    
    # Run for a few seconds to accumulate frames
    logging.info(
        "Capturing frames (at ~%.1f FPS, detecting every %.1f seconds)...",
        1.0 / config.frame_interval_seconds,
        config.detection_interval_seconds
    )
    monitor.run(runtime_seconds=3.0)
    
    # Check status after running
    status = monitor.get_status()
    logging.info("Buffer accumulated %d frames", status["buffer_size"])
    
    # Demonstrate manual recording with pre/post event seconds
    logging.info("Manually triggering recording (pre=%.1fs, post=%.1fs)...",
                 config.pre_event_seconds, config.post_event_seconds)
    output_path = monitor.trigger_manual_recording()
    if output_path:
        logging.info("Recording saved: %s", output_path)
    
    # Demonstrate monitoring enable/disable toggle
    logging.info("\n=== Testing monitoring enable/disable ===")
    monitor.disable_monitoring()
    logging.info("Monitoring disabled - camera still running, but no detection")
    monitor.run(runtime_seconds=2.0)
    
    monitor.enable_monitoring()
    logging.info("Monitoring re-enabled - detection active again")
    monitor.run(runtime_seconds=2.0)
    
    # Final status
    status = monitor.get_status()
    logging.info(
        "\nFinal status: running=%s, monitoring=%s, recordings=%d",
        status["running"], status["monitoring_enabled"], status["recording_count"]
    )
    
    monitor.stop()
    logging.info("=== Demonstration complete ===")



if __name__ == "__main__":
    main()
