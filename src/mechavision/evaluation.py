"""Reproducible synthetic ablation. These figures are not real-engine benchmarks."""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import numpy as np
from .geometry import Geometry,wrap_angle
from .synthetic import Simulator,SimConfig
from .estimators import RawVisualEstimator,MotionEKF


def run_evaluation(seconds:float=24.0,fps:int=30,seed:int=42,
                   out_dir:str|Path|None=None,noise_px:float=3.0):
    if seconds<=0 or fps<=0:raise ValueError("seconds and fps must be positive")
    geo=Geometry()
    sim=Simulator(geo,SimConfig(seed=seed,noise_px=noise_px))
    methods={
        "raw_cv_baseline":RawVisualEstimator(geo),
        "temporal_ekf":MotionEKF(geo,physics=False),
        "physics_ekf":MotionEKF(geo,physics=True),
    }
    rows=[]
    for _ in range(round(seconds*fps)):
        obs=sim.step(1/fps)
        for name,estimator in methods.items():
            est=estimator.update(obs)
            error=abs(math.degrees(wrap_angle(est.theta-obs.truth_theta))) if est.theta is not None else None
            rows.append({"frame":obs.frame_id,"time_s":round(obs.timestamp,6),
                         "method":name,"truth_rad":obs.truth_theta,
                         "theta_rad":est.theta,"omega_rad_s":est.omega,
                         "status":est.status,"error_deg":error,
                         "sigma_deg":math.degrees(est.sigma_theta) if est.sigma_theta is not None else None,
                         "crank_visible":int("crank" in obs.landmarks),
                         "piston_visible":int("piston" in obs.landmarks),
                         "rejected":est.rejected_count})
    summary={}
    for name in methods:
        group=[r for r in rows if r["method"]==name]
        valid=[r["error_deg"] for r in group if r["error_deg"] is not None]
        errs=np.asarray(valid,dtype=float)
        visible=[r for r in group if not r["crank_visible"] and r["piston_visible"]]
        covered=sum(r["theta_rad"] is not None for r in visible)
        summary[name]={
            "mae_deg":float(np.mean(errs)) if len(errs) else None,
            "rmse_deg":float(np.sqrt(np.mean(errs**2))) if len(errs) else None,
            "p95_abs_error_deg":float(np.percentile(errs,95)) if len(errs) else None,
            "availability_pct":100*len(errs)/len(group),
            "occluded_crank_piston_visible_availability_pct":(100*covered/len(visible)) if visible else None,
            "num_valid":len(errs),"num_frames":len(group),
            "rejected_measurements":sum(r["rejected"] for r in group),
        }
    result={"metadata":{"dataset":"SYNTHETIC_ONLY","seconds":seconds,"fps":fps,
                        "seed":seed,"noise_px":noise_px,"geometry":vars(geo),
                        "warning":"No trained AI detector or physical ground-truth evaluation"},
            "methods":summary}
    if out_dir is not None:
        output=Path(out_dir);output.mkdir(parents=True,exist_ok=True)
        with (output/"ablation.csv").open("w",newline="",encoding="utf-8") as fp:
            w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        (output/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result
