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
    buffer = RingBuffer()
    detector = Detector()
    recorder = VideoRecorder(config.recording_dir)
    monitor = MonitorSystem(config, camera, buffer, detector, recorder)

    monitor.start()
    monitor.run(runtime_seconds=5.0)
    monitor.stop()


if __name__ == "__main__":
    main()
