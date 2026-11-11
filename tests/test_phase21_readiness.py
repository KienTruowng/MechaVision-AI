"""Kiểm chứng readiness bằng fixture, không phải kết quả cơ cấu vật lý."""
import json
import time
import cv2
import numpy as np
import pytest
from test_dashboard_v2 import app, window, wait_until
from test_phase2_pipeline import Capture
from mechavision.acquisition import FrameSource
from mechavision.calibration import save_calibration, validate_frame_size
from mechavision.geometry import Geometry


@pytest.mark.parametrize('frame', [None, np.zeros((0, 3, 3), np.uint8), np.zeros((10, 10), np.uint8)])
def test_invalid_frames_release(monkeypatch, frame):
    cap = Capture([])
    cap.read = lambda: (True, frame)
    monkeypatch.setattr(cv2, 'VideoCapture', lambda _: cap)
    with pytest.raises(RuntimeError, match='khung hình lỗi'):
        with FrameSource(0) as source:
            source.read()
    assert cap.released


def test_timestamp_repeated_after_valid_timestamp(monkeypatch):
    cap = Capture([np.zeros((5, 5, 3), np.uint8)] * 3)
    cap.get = lambda key: 25 if key == cv2.CAP_PROP_FPS else 2000
    monkeypatch.setattr(cv2, 'VideoCapture', lambda _: cap)
    with FrameSource('fixture.avi') as source:
        assert [source.read()[1] for _ in range(3)] == pytest.approx([2, 2.04, 2.08])


def test_calibration_roundtrip_and_resolution_guard(tmp_path):
    original = Geometry(axis_deg=12, slider_offset_px=8)
    pts = original.points(.8)
    result = Geometry.from_landmarks(pts['pivot'], pts['crank'], pts['piston'], original.image(100, 0))
    path = tmp_path / 'geometry.json'
    save_calibration(result, path, (960, 540), mm_per_pixel=.5)
    assert Geometry.from_json(path).radius_px == pytest.approx(original.radius_px)
    validate_frame_size(path, 960, 540)
    with pytest.raises(ValueError, match='Độ phân giải'):
        validate_frame_size(path, 640, 400)
    original.to_json(path)
    with pytest.raises(ValueError, match='đã đổi'):
        validate_frame_size(path, 960, 540)
    with pytest.raises(ValueError):
        save_calibration(original, path, (960, 540), float('nan'))


def test_watchdog_requests_cancel_and_ignores_late_sample(window):
    class Stalled:
        last_progress = time.perf_counter() - 16
        stopped = False
        def isRunning(self): return not self.stopped
        def stop(self): self.stopped = True
    worker = Stalled()
    window.worker = worker
    window.state.phase = 'running'
    window._check_worker_timeout()
    assert worker.stopped and window.state.phase == 'error'
    window._on_sample(None, None, None)
    assert window.state.sample_count == 0
    window.worker = None


def test_session_metadata_simulation(window):
    window.start()
    wait_until(lambda: window.state.sample_count >= 4)
    window.stop()
    wait_until(lambda: window.state.phase == 'stopped')
    from pathlib import Path
    meta = json.loads(Path(window.state.log_path).with_suffix('.metadata.json').read_text(encoding='utf-8'))
    assert meta['classification'] == 'simulation'
    assert meta['state'] == 'stopped' and meta['frames'] >= 4
    assert sum(meta['tracking_counts'].values()) == meta['frames']
    assert meta['latency_ms'] is None


def test_blocked_capture_ui_cancel_and_close(window, tmp_path, monkeypatch):
    from threading import Event
    from PySide6.QtTest import QTest
    import mechavision.dashboard_controller as controller
    entered, release = Event(), Event()
    class BlockingCapture:
        closed = False
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): self.closed = True
        def read(self):
            entered.set()
            release.wait(3)
            return None
    monkeypatch.setattr(controller, 'FrameSource', BlockingCapture)
    geometry = tmp_path / 'geometry.json'
    Geometry().to_json(geometry)
    window.geom_path.setText(str(geometry))
    window.source_mode.setCurrentIndex(window.source_mode.findData('camera'))
    window.input_source.setText('0')
    try:
        window.start()
        wait_until(entered.is_set)
        window.worker.last_progress = time.perf_counter() - 16
        window._check_worker_timeout()
        assert window.state.phase == 'error'
        tic = time.perf_counter()
        window.close()
        assert time.perf_counter() - tic < .5
        QTest.qWait(30)  # Luồng sự kiện vẫn hoạt động khi read chưa trả về.
        assert window.worker.isRunning()
    finally:
        release.set()
    wait_until(lambda: not window.worker.isRunning())
    from pathlib import Path
    meta = json.loads(Path(window.state.log_path).with_suffix('.metadata.json').read_text(encoding='utf-8'))
    assert meta['state'] == 'error' and '15' in meta['error']
