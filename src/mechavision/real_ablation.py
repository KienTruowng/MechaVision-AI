"""Paired three-estimator evaluation on the *same recorded real observations*.

Scientific caveats:
- Independent reference angles are supplied by a separate measurement method.
- All parameters are fixed before test; do not tune on test-session labels.
- Wrapped error cannot establish revolution-count accuracy.
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import numpy as np
from .types import Landmark,Observation
from .geometry import Geometry,wrap_angle
from .estimators import RawVisualEstimator,MotionEKF


def _float_or_none(value):
    return None if value is None or str(value).strip()=='' else float(value)


def real_ablation(session_file:str,truth_file:str,geometry_file:str,out_dir:str='outputs/real_ablation'):
    geo=Geometry.from_json(geometry_file)
    with Path(truth_file).open(newline='',encoding='utf-8-sig') as fp:
        reader=csv.DictReader(fp)
        if not reader.fieldnames or 'frame' not in reader.fieldnames or not ({'theta_deg','theta_rad'}&set(reader.fieldnames)):
            raise ValueError('Ground truth must contain frame,theta_deg or frame,theta_rad')
        truth={}
        for row in reader:
            if not row.get('frame'):continue
            deg=_float_or_none(row.get('theta_deg'))
            rad=_float_or_none(row.get('theta_rad'))
            if deg is None and rad is None:continue
            truth[int(row['frame'])]=math.radians(deg) if deg is not None else rad
    methods={'raw_visual':RawVisualEstimator(geo),
             'temporal_ekf':MotionEKF(geo,physics=False),
             'physics_ekf':MotionEKF(geo,physics=True)}
    outrows=[]
    with Path(session_file).open(newline='',encoding='utf-8-sig') as fp:
        for row in csv.DictReader(fp):
            try:
                frame=int(row['frame']);t=float(row['time_s'])
            except (ValueError,KeyError):continue
            landmarks={}
            for key in ('pivot','crank','piston'):
                x=_float_or_none(row.get('obs_'+key+'_x'))
                y=_float_or_none(row.get('obs_'+key+'_y'))
                cf=_float_or_none(row.get('obs_'+key+'_conf'))
                if x is not None and y is not None:
                    landmarks[key]=Landmark(x,y,cf if cf is not None else 1.0)
            obs=Observation(t,landmarks,frame_id=frame)
            for name,method in methods.items():
                estimate=method.update(obs)
                if frame not in truth:continue
                reference=truth[frame]
                error=(abs(math.degrees(wrap_angle(estimate.theta-reference)))
                       if estimate.theta is not None else None)
                outrows.append({'frame':frame,'time_s':t,'method':name,
                                'status':estimate.status,'theta_rad':estimate.theta,
                                'reference_theta_rad':reference,'abs_error_deg':error,
                                'crank_visible':int('crank' in landmarks),
                                'piston_visible':int('piston' in landmarks)})
    if not outrows:raise ValueError('No overlapping frame IDs between recorded observations and reference labels')
    summary={}
    for name in methods:
        group=[row for row in outrows if row['method']==name]
        errs=np.array([row['abs_error_deg'] for row in group if row['abs_error_deg'] is not None],dtype=float)
        subgroup=[row for row in group if not row['crank_visible'] and row['piston_visible']]
        summary[name]={
            'reference_frames':len(group),'valid_estimates':len(errs),
            'coverage_pct':100*len(errs)/len(group),
            'mae_deg':float(np.mean(errs)) if len(errs) else None,
            'rmse_deg':float(np.sqrt(np.mean(errs**2))) if len(errs) else None,
            'p95_abs_error_deg':float(np.percentile(errs,95)) if len(errs) else None,
            'crank_occluded_piston_visible_coverage_pct':(
                100*sum(r['theta_rad'] is not None for r in subgroup)/len(subgroup)
                if subgroup else None),
        }
    result={'dataset':'RECORDED_OBSERVATIONS_INDEPENDENT_REFERENCE',
            'source_session':session_file,'ground_truth':truth_file,
            'geometry':geometry_file,'methods':summary,
            'caveats':['Angular accuracy is wrapped modulo 360 degrees',
                       'Ground-truth method and its precision must be documented',
                       'Uncertainty calibration and inference latency need separate tests']}
    dest=Path(out_dir);dest.mkdir(parents=True,exist_ok=True)
    with (dest/'real_ablation.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(outrows[0].keys()));w.writeheader();w.writerows(outrows)
    (dest/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
