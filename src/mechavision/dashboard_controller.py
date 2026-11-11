"""Controller chạy nền; giữ nguyên luồng nhận diện, ước lượng và ghi CSV."""

import time
from threading import Event
from PySide6.QtCore import QThread, Signal
from .geometry import Geometry
from .session_metadata import SessionMetadata
from .synthetic import Simulator, SimConfig, draw_mechanism
from .acquisition import FrameSource
from .processing import Processor
from .detection import make_detector, draw_observations
from .render import twin_frame, decorate_video


class Worker(QThread):
    sample = Signal(object, object, object)
    raw_frame = Signal(object)
    failed = Signal(str)
    ended = Signal()

    def __init__(
        self, mode, source, detector, weights, geometry_path, log_path, device
    ):
        super().__init__()
        self.mode = mode
        self.source = source
        self.detector_name = detector
        self.weights = weights
        self.geometry_path = geometry_path
        self.log_path = log_path
        self.device = device
        self._stop = False
        self.cancel_reason = None
        self._paused = Event()
        self._wake = Event()
        self.last_progress = time.perf_counter()

    def set_paused(self, paused):
        """Video giữ vị trí; camera tiếp tục đọc và bỏ khung khi tạm dừng."""
        self._paused.set() if paused else self._paused.clear()
        self._wake.set()

    def _wait_active(self):
        while self._paused.is_set() and not self._stop:
            self.last_progress = time.perf_counter()
            self._wake.wait(0.05)
            self._wake.clear()
        return not self._stop

    def _pace(self, seconds):
        deadline = time.perf_counter() + max(0, seconds)
        while not self._stop:
            self.last_progress = time.perf_counter()
            if self._paused.is_set():
                return self._wait_active()
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break
            self._wake.wait(min(remaining, 0.05))
            self._wake.clear()
        return not self._stop

    def stop(self):
        self._stop = True
        self._wake.set()

    def run(self):
        processor = None
        metadata = None
        error = None
        try:
            geo = (
                Geometry()
                if self.mode == "simulation"
                else Geometry.from_json(self.geometry_path)
            )
            processor = Processor(geo, self.log_path)
            if self.log_path:
                metadata = SessionMetadata(self.log_path, self.mode, self.source, self.detector_name, self.device, geo)
            if self.mode == "simulation":
                simulator = Simulator(geo, SimConfig(seed=42))
                while not self._stop:
                    if not self._wait_active():
                        break
                    t0 = time.perf_counter()
                    obs = simulator.step(1 / 30)
                    metrics = processor.step(obs)
                    if metadata:
                        metadata.record(obs, metrics["physics"])
                    self.last_progress = time.perf_counter()
                    frame = draw_mechanism(geo, obs.truth_theta, 900, 520)
                    self.raw_frame.emit(frame.copy())
                    draw_observations(frame, obs)
                    est = metrics["physics"]
                    twin = twin_frame(geo, est)
                    decorate_video(frame, est.status, metrics["fps"])
                    self.sample.emit(
                        frame,
                        twin,
                        {"observation": obs, "metrics": metrics, "synthetic": True},
                    )
                    self.msleep(
                        max(1, int(1000 / 30 - (time.perf_counter() - t0) * 1000))
                    )
            else:
                detector = make_detector(self.detector_name, self.weights, self.device)
                src = int(self.source) if self.mode == "camera" else self.source
                with FrameSource(src) as capture:
                    checked_size = None
                    previous_ts = None
                    previous_wall = None
                    while not self._stop:
                        if self.mode == "video" and not self._wait_active():
                            break
                        sample = capture.read()
                        self.last_progress = time.perf_counter()
                        if sample is None:
                            break
                        frame, ts, index = sample
                        from .calibration import validate_frame_size
                        if checked_size != frame.shape[:2]:
                            validate_frame_size(self.geometry_path, frame.shape[1], frame.shape[0])
                            checked_size = frame.shape[:2]
                            if metadata:
                                metadata.data['source_resolution'] = [frame.shape[1], frame.shape[0]]
                                metadata.data['calibration_path'] = str(self.geometry_path)
                                metadata.save()
                        if self._stop:
                            break
                        if self.mode == "camera" and self._paused.is_set():
                            self.msleep(5)
                            continue
                        if self.mode == "video" and previous_ts is not None:
                            if not self._pace(ts - previous_ts - (time.perf_counter() - previous_wall)):
                                break
                        previous_ts, previous_wall = ts, time.perf_counter()
                        self.raw_frame.emit(frame.copy())
                        obs = detector.detect(frame, ts, index)
                        metrics = processor.step(obs)
                        if metadata:
                            metadata.record(obs, metrics["physics"])
                        est = metrics["physics"]
                        overlay = draw_observations(frame.copy(), obs)
                        decorate_video(overlay, est.status, metrics["fps"])
                        twin = twin_frame(geo, est)
                        self.sample.emit(
                            overlay,
                            twin,
                            {
                                "observation": obs,
                                "metrics": metrics,
                                "synthetic": False,
                            },
                        )
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            self.failed.emit(error)
        finally:
            try:
                if processor:
                    processor.close()
                if metadata:
                    error = error or self.cancel_reason
                    metadata.finish("error" if error else "stopped" if self._stop else "eof", error)
            except Exception as cleanup_error:
                self.failed.emit(f"Lỗi lưu/đóng phiên: {cleanup_error}")
            finally:
                self.ended.emit()


class EvaluationWorker(QThread):
    """Chạy nguyên quy trình đánh giá hiện có ngoài luồng giao diện."""

    completed = Signal(object, str)
    failed = Signal(str)

    def __init__(self, mode, parameters, output):
        super().__init__()
        self.mode = mode
        self.parameters = dict(parameters)
        self.output = output

    def run(self):
        try:
            if self.mode == "synthetic":
                from .evaluation import run_evaluation

                result = run_evaluation(out_dir=self.output, **self.parameters)
            else:
                from .real_ablation import real_ablation

                result = real_ablation(out_dir=self.output, **self.parameters)
            self.completed.emit(result, self.output)
        except Exception as error:
            self.failed.emit(f"{type(error).__name__}: {error}")
