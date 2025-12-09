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


def main() -> None:
    config = AppConfig.load()
    camera = CameraStream(config.camera_source)
    
    # Calculate buffer size based on retention time and frame capture rate
    retention_seconds = max(
        config.pre_event_seconds + config.post_event_seconds,
        1.0,
    )
    frame_interval = max(config.frame_interval_seconds, 1e-3)
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

    monitor.start()
    
    # Run for a few seconds to accumulate frames, then manually trigger recording
    logging.info(
        "Running monitor (capturing at ~%.1f FPS, detecting every %.1f seconds)...",
        1.0 / config.frame_interval_seconds,
        config.detection_interval_seconds
    )
    monitor.run(runtime_seconds=3.0)
    
    # Manually trigger a recording to demonstrate functionality
    logging.info("Manually triggering recording of buffered frames...")
    frames = buffer.snapshot()
    if frames:
        logging.info("Buffer contains %d frames", len(frames))
        output_path = recorder.record_event(frames)
        if output_path:
            logging.info("Recording saved successfully: %s", output_path)
    
    # Continue running for a bit more
    monitor.run(runtime_seconds=2.0)
    monitor.stop()


if __name__ == "__main__":
    main()
