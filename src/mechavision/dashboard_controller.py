"""Controller chạy nền; giữ nguyên luồng nhận diện, ước lượng và ghi CSV."""

import time
from threading import Event
from PySide6.QtCore import QThread, Signal
from .geometry import Geometry
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
        self._paused = Event()
        self._wake = Event()

    def set_paused(self, paused):
        """Video giữ vị trí; camera tiếp tục đọc và bỏ khung khi tạm dừng."""
        self._paused.set() if paused else self._paused.clear()
        self._wake.set()

    def _wait_active(self):
        while self._paused.is_set() and not self._stop:
            self._wake.wait(0.05)
            self._wake.clear()
        return not self._stop

    def _pace(self, seconds):
        deadline = time.perf_counter() + max(0, seconds)
        while not self._stop:
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
        try:
            geo = (
                Geometry()
                if self.mode == "simulation"
                else Geometry.from_json(self.geometry_path)
            )
            processor = Processor(geo, self.log_path)
            if self.mode == "simulation":
                simulator = Simulator(geo, SimConfig(seed=42))
                while not self._stop:
                    if not self._wait_active():
                        break
                    t0 = time.perf_counter()
                    obs = simulator.step(1 / 30)
                    metrics = processor.step(obs)
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
                    previous_ts = None
                    previous_wall = None
                    while not self._stop:
                        if self.mode == "video" and not self._wait_active():
                            break
                        sample = capture.read()
                        if sample is None:
                            break
                        frame, ts, index = sample
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
            self.failed.emit(f"{type(e).__name__}: {e}")
        finally:
            if processor:
                processor.close()
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
