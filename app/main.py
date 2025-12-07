from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Optional
from collections import deque


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


@dataclass
class AppConfig:
	"""Runtime configuration for the monitoring stack."""

	recording_dir: Path = Path("recordings")
	pre_event_seconds: float = 10.0
	post_event_seconds: float = 10.0
	enable_monitoring: bool = True
	frame_interval_seconds: float = 1.0
	camera_source: Any = 0

	@classmethod
	def load(cls) -> "AppConfig":
		# Placeholder for real configuration loading logic.
		config = cls()
		config.recording_dir.mkdir(parents=True, exist_ok=True)
		return config


class CameraStream:
	"""Placeholder camera stream that emits dummy frames."""

	def __init__(self, source: Any = 0) -> None:
		self.source = source
		self._running = False

	def start(self) -> None:
		logging.info("CameraStream started (source=%s)", self.source)
		self._running = True

	def stop(self) -> None:
		logging.info("CameraStream stopped")
		self._running = False

	def read_frame(self) -> dict[str, Any]:
		if not self._running:
			raise RuntimeError("CameraStream is not running")
		return {"timestamp": time.time(), "data": None}


class RingBuffer:
	"""Simple deque-based buffer for recent frames."""

	def __init__(self, max_frames: int = 60) -> None:
		self._frames: Deque[dict[str, Any]] = deque(maxlen=max_frames)

	def append(self, frame: dict[str, Any]) -> None:
		self._frames.append(frame)

	def snapshot(self) -> list[dict[str, Any]]:
		return list(self._frames)


class Detector:
	"""Strategy interface for event detection."""

	def should_record(self, frame: dict[str, Any]) -> bool:
		return False


class VideoRecorder:
	"""Responsible for writing video clips (placeholder)."""

	def __init__(self, output_dir: Path) -> None:
		self.output_dir = output_dir

	def record_event(self, frames: list[dict[str, Any]]) -> None:
		logging.info("VideoRecorder received %d frames (placeholder)", len(frames))


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
