"""Chuỗi mô phỏng có nhãn và có thể tái lập; không phải bằng chứng thực nghiệm vật lý."""
from __future__ import annotations
from .i18n import put_text, KEYPOINT_LABELS
from dataclasses import dataclass
import math
import numpy as np
from .geometry import Geometry
from .types import Observation, Landmark


@dataclass
class SimConfig:
    noise_px: float = 2.5
    crank_occlusion_rate: float = 0.12
    piston_occlusion_rate: float = 0.16
    outlier_rate: float = 0.02
    seed: int = 42


class Simulator:
    def __init__(self, geometry: Geometry, cfg: SimConfig | None = None):
        self.geometry = geometry
        self.cfg = cfg or SimConfig()
        self.rng = np.random.default_rng(self.cfg.seed)
        self.t = 0.0
        self.theta = 0.30
        self.frame_id = 0

    @staticmethod
    def angular_speed(t: float) -> float:
        """Tốc độ biến thiên, có khoảng dừng ngắn và đảo chiều."""
        if 7.0 < t < 8.2:
            return 0.0
        if 14.0 < t < 17.0:
            return -1.2 - 0.3*math.sin(t*1.3)
        return 1.5 + 0.55*math.sin(t*0.65) + 0.25*math.sin(t*2.4)

    def step(self, dt: float = 1/30) -> Observation:
        dt = max(0.001, min(0.15, dt))
        mid = self.t + dt/2
        self.theta += self.angular_speed(mid) * dt
        self.t += dt
        self.frame_id += 1
        positions = self.geometry.points(self.theta)
        result = {}
        for key,point in positions.items():
            drop_rate = {"pivot":0.0, "crank":self.cfg.crank_occlusion_rate,
                         "piston":self.cfg.piston_occlusion_rate}[key]
            # Khoảng che khuất cố định và một số lần che khuất độc lập ngẫu nhiên.
            interval_occlusion = (key == "crank" and 3.2 < self.t < 4.5) or (key == "piston" and 10 < self.t < 11.8)
            if interval_occlusion or self.rng.random() < drop_rate:
                continue
            xy = point + self.rng.normal(0, self.cfg.noise_px, size=2)
            if key != "pivot" and self.rng.random() < self.cfg.outlier_rate:
                xy += self.rng.normal(0, 70, size=2)
            result[key] = Landmark(float(xy[0]),float(xy[1]), 0.85)
        return Observation(self.t, result, truth_theta=self.theta,frame_id=self.frame_id)


def draw_mechanism(geometry: Geometry, theta: float, width=900, height=520,
                   observation: Observation | None = None, title="CƠ CẤU MÔ PHỎNG") -> np.ndarray:
    import cv2
    frame=np.full((height,width,3),(31,19,7),dtype=np.uint8)
    points = geometry.points(theta)
    def pos(p): return tuple(np.rint(p).astype(int))
    origin, crank, piston = map(lambda k:pos(points[k]), ("pivot","crank","piston"))
    cv2.line(frame,(0,origin[1]),(width,origin[1]),(65,67,78),1)
    cv2.circle(frame,origin,round(geometry.radius_px), (50,67,90),1,cv2.LINE_AA)
    cv2.line(frame,origin,crank,(255,143,67),9,cv2.LINE_AA)
    cv2.line(frame,crank,piston,(237,212,80),8,cv2.LINE_AA)
    cv2.rectangle(frame,(piston[0]-18,piston[1]-24),(piston[0]+18,piston[1]+24),(104,73,34),-1)
    cv2.rectangle(frame,(piston[0]-18,piston[1]-24),(piston[0]+18,piston[1]+24),(237,212,80),2)
    for p,col in ((origin,(239,242,248)),(crank,(233,187,99)),(piston,(101,219,247))):
        cv2.circle(frame,p,7,col,-1,cv2.LINE_AA)
    put_text(frame,title,(22,33),cv2.FONT_HERSHEY_SIMPLEX,.65,(200,208,224),2,cv2.LINE_AA)
    put_text(frame,"DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI PHÉP ĐO THỰC",(22,height-24),cv2.FONT_HERSHEY_SIMPLEX,.5,(148,165,188),1,cv2.LINE_AA)
    if observation:
        for name,p in observation.landmarks.items():
            pp=(round(p.x),round(p.y))
            cv2.circle(frame,pp,9,(61,214,123),2,cv2.LINE_AA)
            put_text(frame,KEYPOINT_LABELS.get(name, name), (pp[0]+10,pp[1]-10),cv2.FONT_HERSHEY_SIMPLEX,.45,(61,214,123),1,cv2.LINE_AA)
    return frame
