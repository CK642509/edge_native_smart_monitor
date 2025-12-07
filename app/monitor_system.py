from __future__ import annotations

import logging
import time
from typing import Optional

from app.camera_stream import CameraStream
from app.config import AppConfig
from app.detector import Detector
from app.ring_buffer import RingBuffer
from app.video_recorder import VideoRecorder


class MonitorSystem:
    """Facade coordinating camera, buffer, detector, and recorder."""

    def __init__(
        self,
        config: AppConfig,
        camera: CameraStream,
        buffer: RingBuffer,
        detector: Detector,
        recorder: VideoRecorder,
    ) -> None:
        self.config = config
        self.camera = camera
        self.buffer = buffer
        self.detector = detector
        self.recorder = recorder
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self.camera.start()
        self._running = True
        logging.info("MonitorSystem started")

    def stop(self) -> None:
        if not self._running:
            return
        self.camera.stop()
        self._running = False
        logging.info("MonitorSystem stopped")

    def tick(self) -> None:
        if not self._running:
            return
        frame = self.camera.read_frame()
        self.buffer.append(frame)
        if self.detector.should_record(frame):
            self.recorder.record_event(self.buffer.snapshot())

    def run(self, runtime_seconds: Optional[float] = None) -> None:
        start_time = time.time()
        try:
            while self._running:
                self.tick()
                if runtime_seconds is not None and time.time() - start_time >= runtime_seconds:
                    break
                time.sleep(self.config.frame_interval_seconds)
        except KeyboardInterrupt:
            logging.info("MonitorSystem interrupted by user")
