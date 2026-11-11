"""Trạng thái hiển thị của phiên; chỉ lưu kết quả do Processor cung cấp."""

from collections import deque
import math


class DashboardState:
    HISTORY_LIMIT = 3600
    SERIES = (
        "time",
        "raw_angle",
        "temporal_angle",
        "physics_angle",
        "temporal_rpm",
        "physics_rpm",
        "temporal_sigma",
        "physics_sigma",
        "discrepancy",
        "piston_observed",
        "piston_estimated",
        "fps",
    )

    def __init__(self):
        self.series = {name: deque(maxlen=self.HISTORY_LIMIT) for name in self.SERIES}
        self.reset()

    def reset(self, mode="simulation", log_path=""):
        for values in self.series.values():
            values.clear()
        self.phase = "idle"
        self.mode = mode
        self.log_path = log_path
        self.sample_count = 0
        self.accepted_total = 0
        self.rejected_total = 0
        self.observation = None
        self.metrics = None
        self.error = ""

    @staticmethod
    def degrees(value):
        return math.degrees(value) if value is not None else None

    def append(self, observation, metrics):
        self.observation = observation
        self.metrics = metrics
        self.sample_count += 1
        physics, temporal = metrics["physics"], metrics["temporal"]
        self.accepted_total += physics.observation_count
        self.rejected_total += physics.rejected_count
        values = {
            "time": observation.timestamp,
            "raw_angle": self.degrees(metrics["measured_theta"]),
            "temporal_angle": self.degrees(temporal.theta),
            "physics_angle": self.degrees(physics.theta),
            "temporal_rpm": temporal.rpm,
            "physics_rpm": physics.rpm,
            "temporal_sigma": self.degrees(temporal.sigma_theta),
            "physics_sigma": self.degrees(physics.sigma_theta),
            "discrepancy": physics.kinematic_discrepancy_px,
            "piston_observed": metrics["observed_x"],
            "piston_estimated": metrics["predicted_x"],
            "fps": metrics["fps"],
        }
        for name, value in values.items():
            self.series[name].append(float("nan") if value is None else value)
        return values
