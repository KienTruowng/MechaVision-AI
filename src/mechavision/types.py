"""Kiểu dữ liệu quan sát và kết quả ước lượng. Đơn vị: pixel, giây, radian."""
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
    truth_theta: Optional[float] = None  # Chỉ dùng cho mô phỏng; bộ ước lượng không sử dụng.
    frame_id: int = 0


@dataclass
class Estimate:
    timestamp: float
    theta: Optional[float] = None  # Góc liên tục theo radian, không giới hạn trong một vòng.
    omega: Optional[float] = None  # Radian trên giây.
    sigma_theta: Optional[float] = None
    status: str = "UNINITIALIZED"  # Theo dõi / dự báo / mất dấu / chưa khởi tạo (giữ nguyên mã).
    observation_count: int = 0
    rejected_count: int = 0
    fit_residual_px: Optional[float] = None
    measured_crank_theta: Optional[float] = None
    kinematic_discrepancy_px: Optional[float] = None

    @property
    def rpm(self) -> Optional[float]:
        return None if self.omega is None else self.omega * 60.0 / (2.0 * 3.141592653589793)
