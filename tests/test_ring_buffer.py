"""Unit tests for RingBuffer module."""

from __future__ import annotations

import time
from threading import Thread

import numpy as np
import pytest

from app.ring_buffer import RingBuffer


class TestRingBuffer:
    """Test cases for RingBuffer."""

    def test_buffer_initialization(self) -> None:
        """Test buffer can be initialized with valid parameters."""
        buffer = RingBuffer(retention_seconds=5.0, max_frames=100)
        assert buffer.retention_seconds == 5.0
        assert buffer.max_frames == 100
        assert len(buffer) == 0

    def test_buffer_requires_eviction_mechanism(self) -> None:
        """Test that buffer requires at least one eviction mechanism."""
        with pytest.raises(ValueError, match="Either retention_seconds must be positive"):
            RingBuffer(retention_seconds=0, max_frames=None)

    def test_append_and_snapshot(self) -> None:
        """Test appending frames and taking snapshots."""
        buffer = RingBuffer(retention_seconds=10.0)
        
        frame1 = {"data": np.zeros((480, 640, 3)), "frame_number": 1}
        frame2 = {"data": np.zeros((480, 640, 3)), "frame_number": 2}
        
        buffer.append(frame1)
        buffer.append(frame2)
        
        assert len(buffer) == 2
        snapshot = buffer.snapshot()
        assert len(snapshot) == 2
        assert snapshot[0]["frame_number"] == 1
        assert snapshot[1]["frame_number"] == 2

    def test_auto_timestamp_addition(self) -> None:
        """Test that timestamp is added automatically if missing."""
        buffer = RingBuffer(retention_seconds=10.0)
        
        frame = {"data": np.zeros((480, 640, 3))}
        before = time.time()
        buffer.append(frame)
        after = time.time()
        
        snapshot = buffer.snapshot()
        assert len(snapshot) == 1
        assert "timestamp" in snapshot[0]
        assert before <= snapshot[0]["timestamp"] <= after

    def test_time_based_eviction(self) -> None:
        """Test that old frames are evicted based on retention time."""
        buffer = RingBuffer(retention_seconds=0.5)
        
        # Add frame with old timestamp
        old_frame = {"timestamp": time.time() - 1.0, "frame_number": 1}
        buffer.append(old_frame)
        
        # Add current frame
        current_frame = {"timestamp": time.time(), "frame_number": 2}
        buffer.append(current_frame)
        
        snapshot = buffer.snapshot()
        # Old frame should be evicted
        assert len(snapshot) == 1
        assert snapshot[0]["frame_number"] == 2

    def test_max_frames_eviction(self) -> None:
        """Test that frames are evicted when max_frames is exceeded."""
        buffer = RingBuffer(retention_seconds=100.0, max_frames=3)
        
        for i in range(5):
            frame = {"frame_number": i + 1}
            buffer.append(frame)
        
        snapshot = buffer.snapshot()
        # Should only keep last 3 frames
        assert len(snapshot) == 3
        assert snapshot[0]["frame_number"] == 3
        assert snapshot[1]["frame_number"] == 4
        assert snapshot[2]["frame_number"] == 5

    def test_thread_safety(self) -> None:
        """Test that buffer is thread-safe for concurrent access."""
        buffer = RingBuffer(retention_seconds=10.0, max_frames=1000)
        errors = []
        
        def writer_thread(start_num: int) -> None:
            try:
                for i in range(50):
                    frame = {"frame_number": start_num + i}
                    buffer.append(frame)
            except Exception as e:
                errors.append(e)
        
        def reader_thread() -> None:
            try:
                for _ in range(50):
                    buffer.snapshot()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Start multiple writer and reader threads
        threads = [
            Thread(target=writer_thread, args=(0,)),
            Thread(target=writer_thread, args=(1000,)),
            Thread(target=reader_thread),
            Thread(target=reader_thread),
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No errors should have occurred
        assert len(errors) == 0
        # Buffer should have frames from both writers
        assert len(buffer) > 0

    def test_snapshot_is_copy(self) -> None:
        """Test that snapshot returns a copy, not the original buffer."""
        buffer = RingBuffer(retention_seconds=10.0)
        
        frame = {"frame_number": 1}
        buffer.append(frame)
        
        snapshot1 = buffer.snapshot()
        snapshot2 = buffer.snapshot()
        
        # Snapshots should be different lists
        assert snapshot1 is not snapshot2
        # But have equal content
        assert snapshot1[0]["frame_number"] == snapshot2[0]["frame_number"]

    def test_empty_buffer_snapshot(self) -> None:
        """Test that snapshot of empty buffer returns empty list."""
        buffer = RingBuffer(retention_seconds=10.0)
        
        snapshot = buffer.snapshot()
        assert isinstance(snapshot, list)
        assert len(snapshot) == 0

    def test_combined_eviction(self) -> None:
        """Test that both time-based and count-based eviction work together."""
        buffer = RingBuffer(retention_seconds=1.0, max_frames=5)
        
        # Add 10 frames
        for i in range(10):
            frame = {"frame_number": i + 1, "timestamp": time.time()}
            buffer.append(frame)
            time.sleep(0.05)
        
        snapshot = buffer.snapshot()
        # Should be limited by max_frames
        assert len(snapshot) <= 5
