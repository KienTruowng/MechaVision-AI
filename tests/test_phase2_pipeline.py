"""Fixture tổng hợp qua decoder thật; không phải thực nghiệm LEGO."""
import csv
import time

import cv2
import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from test_dashboard_v2 import app, window, wait_until
from mechavision.acquisition import FrameSource
from mechavision.geometry import Geometry


class Capture:
    def __init__(self, frames, opened=True):
        self.frames = iter(frames)
        self.opened = opened
        self.released = False

    def isOpened(self): return self.opened
    def set(self, *_): pass
    def get(self, key): return 25 if key == cv2.CAP_PROP_FPS else 0
    def read(self):
        frame = next(self.frames, None)
        return frame is not None, frame
    def release(self): self.released = True


def test_camera_transient_drop_and_disconnect(monkeypatch):
    frame = np.zeros((10, 10, 3), np.uint8)
    cap = Capture([None, frame, None, None, None])
    monkeypatch.setattr(cv2, 'VideoCapture', lambda _: cap)
    with pytest.raises(RuntimeError, match='Mất khung'):
        with FrameSource(0) as source:
            assert source.read()[0] is frame
            source.read()
    assert cap.released


def test_file_timestamp_fallback_and_eof(monkeypatch):
    frame = np.zeros((10, 10, 3), np.uint8)
    cap = Capture([frame, frame, frame])
    monkeypatch.setattr(cv2, 'VideoCapture', lambda _: cap)
    with FrameSource('fixture.avi') as source:
        times = [source.read()[1] for _ in range(3)]
        assert times == pytest.approx([1e-6, .04, .08])
        assert source.read() is None
    assert cap.released


def test_failed_open_releases_handle(monkeypatch):
    cap = Capture([], opened=False)
    monkeypatch.setattr(cv2, 'VideoCapture', lambda _: cap)
    with pytest.raises(RuntimeError, match='Không mở'):
        FrameSource(0)
    assert cap.released


def make_video(folder):
    geo = Geometry()
    geometry = folder / 'geometry.json'
    geo.to_json(geometry)
    video = folder / 'SYNTHETIC_ONLY.avi'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 30, (640, 400))
    assert writer.isOpened()
    for i in range(90):
        frame = np.full((400, 640, 3), 20, np.uint8)
        for name, point in geo.points(.4 + i * .025).items():
            if 35 <= i < 65 or (20 <= i < 35 and name == 'piston'):
                continue
            color = {'pivot': (0, 0, 255), 'crank': (0, 255, 0), 'piston': (255, 0, 0)}[name]
            cv2.circle(frame, tuple(np.rint(point).astype(int)), 11, color, -1)
        cv2.putText(frame, 'SYNTHETIC TEST ONLY', (10, 390), cv2.FONT_HERSHEY_SIMPLEX, .6, (200, 200, 200), 1)
        writer.write(frame)
    writer.release()
    return video, geometry


def test_video_pause_occlusion_recovery_twin_csv(window, tmp_path):
    video, geometry = make_video(tmp_path)
    window.source_mode.setCurrentIndex(window.source_mode.findData('video'))
    window.input_source.setText(str(video))
    window.geom_path.setText(str(geometry))
    window.detector_mode.setCurrentIndex(window.detector_mode.findData('color'))
    samples = []
    window.start()
    window.worker.sample.connect(lambda frame, twin, data: samples.append((twin, data)))
    wait_until(lambda: window.state.sample_count >= 8)
    QTest.mouseClick(window.start_btn, Qt.LeftButton)
    assert window.state.phase == 'paused'
    count = window.state.sample_count
    QTest.qWait(200)
    assert window.state.sample_count == count
    window.navigate(1)
    QTest.mouseClick(window.start_btn, Qt.LeftButton)
    started = time.perf_counter()
    wait_until(lambda: window.state.phase == 'stopped', timeout=7000)
    assert time.perf_counter() - started > 1.5  # Phát theo thời gian nguồn, không giải mã dồn dập
    assert not window.test_errors
    assert samples and all(twin.shape == (390, 620, 3) for twin, _ in samples)
    states = [data['metrics']['physics'].status for _, data in samples]
    assert 'PREDICTED' in states and 'LOST' in states and states[-1] == 'TRACKING'
    rows = list(csv.DictReader(open(window.state.log_path, encoding='utf-8')))
    assert len(rows) == 90
    assert all(not row['truth_rad_synthetic_only'] for row in rows)
    assert not rows[25]['obs_piston_x'] and rows[25]['theta_rad']
    assert any(row['status'] == 'LOST' and not row['theta_rad'] for row in rows)
    assert rows[-1]['status'] == 'TRACKING'


def test_stop_while_paused(window):
    window.start()
    wait_until(lambda: window.state.sample_count >= 3)
    window.start()
    assert window.state.phase == 'paused'
    window.stop()
    wait_until(lambda: window.state.phase == 'stopped')
    assert window.start_btn.text() == 'Bắt đầu phiên'
