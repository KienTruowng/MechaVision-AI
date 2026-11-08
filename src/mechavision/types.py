"""Typed observations and estimation results. Units are pixels, seconds, radians."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

Point = tuple[float, float]


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float
    confidence: float = 1.0

    @property
    def xy(self) -> Point:
        return (self.x, self.y)


@dataclass
class Observation:
    timestamp: float
    landmarks: dict[str, Landmark] = field(default_factory=dict)
    truth_theta: Optional[float] = None  # synthetic only; never used by estimators
    frame_id: int = 0


@dataclass
class Estimate:
    timestamp: float
    theta: Optional[float] = None  # unwrapped radians
    omega: Optional[float] = None  # radians per second
    sigma_theta: Optional[float] = None
    status: str = "UNINITIALIZED"  # TRACKING / PREDICTED / LOST / UNINITIALIZED
    observation_count: int = 0
    rejected_count: int = 0
    fit_residual_px: Optional[float] = None
    measured_crank_theta: Optional[float] = None
    kinematic_discrepancy_px: Optional[float] = None

    @property
    def rpm(self) -> Optional[float]:
        return None if self.omega is None else self.omega * 60.0 / (2.0 * 3.141592653589793)
