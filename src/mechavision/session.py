"""Ghi phiên CSV. Phép đo thiếu được để trống, không thay bằng số không."""
from __future__ import annotations
import csv
from pathlib import Path
from .types import Observation,Estimate

FIELDS=("frame","time_s","status","theta_rad","rpm","sigma_deg","fit_residual_px",
        "kinematic_discrepancy_px","obs_pivot_x","obs_pivot_y","obs_crank_x","obs_crank_y",
        "obs_piston_x","obs_piston_y","obs_pivot_conf","obs_crank_conf",
        "obs_piston_conf","truth_rad_synthetic_only")


class SessionWriter:
    def __init__(self,path:str|Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.fp=self.path.open("w",newline="",encoding="utf-8")
        self.writer=csv.DictWriter(self.fp,fieldnames=FIELDS)
        self.writer.writeheader()

    def write(self,obs:Observation,estimate:Estimate):
        import math
        data={"frame":obs.frame_id,"time_s":obs.timestamp,"status":estimate.status,
              "theta_rad":estimate.theta,"rpm":estimate.rpm,
              "sigma_deg":math.degrees(estimate.sigma_theta) if estimate.sigma_theta is not None else None,
              "fit_residual_px":estimate.fit_residual_px,
              "kinematic_discrepancy_px":estimate.kinematic_discrepancy_px,
              "truth_rad_synthetic_only":obs.truth_theta}
        for key in ("pivot","crank","piston"):
            p=obs.landmarks.get(key)
            data[f"obs_{key}_x"]=p.x if p else None
            data[f"obs_{key}_y"]=p.y if p else None
            data[f"obs_{key}_conf"]=p.confidence if p else None
        self.writer.writerow(data)

    def close(self):
        if not self.fp.closed:
            self.fp.close()

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
