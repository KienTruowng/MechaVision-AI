"""Research-grade real-data replay: exactly the same saved observations for all methods.

Ground truth MUST be independently collected, e.g. separately reviewed human
annotations or reference encoder. A synthetic 'truth_rad_synthetic_only' column
is deliberately NEVER used as real ground truth.
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import numpy as np
from .types import Observation,Landmark
from .geometry import Geometry,wrap_angle
from .estimators import RawVisualEstimator,MotionEKF


def _read_truth(path):
    truth={}
    with open(path,encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            if not row.get('frame'):continue
            if row.get('theta_deg') not in (None,''):
                angle=math.radians(float(row['theta_deg']))
            elif row.get('theta_rad') not in (None,''):
                angle=float(row['theta_rad'])
            else:raise ValueError('Ground truth requires theta_deg or theta_rad')
            truth[int(row['frame'])]=angle
    if not truth:raise ValueError('Ground truth is empty')
    return truth


def replay_real(session_file:str,geometry_file:str,ground_truth_file:str,out_dir:str):
    geo=Geometry.from_json(geometry_file)
    truth=_read_truth(ground_truth_file)
    methods={
        'raw_cv_baseline':RawVisualEstimator(geo),
        'temporal_ekf':MotionEKF(geo,physics=False),
        'physics_ekf':MotionEKF(geo,physics=True),
    }
    output=Path(out_dir);output.mkdir(parents=True,exist_ok=True)
    results=[]
    with open(session_file,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        for row in reader:
            frame=int(row['frame'])
            landmarks={}
            for k in ('pivot','crank','piston'):
                if row.get(f'obs_{k}_x') in (None,'') or row.get(f'obs_{k}_y') in (None,''):
                    continue
                conf=row.get(f'obs_{k}_conf')
                landmarks[k]=Landmark(float(row[f'obs_{k}_x']),float(row[f'obs_{k}_y']),
                                      float(conf) if conf not in ('',None) else 1.)
            obs=Observation(float(row['time_s']),landmarks,frame_id=frame)
            for name,method in methods.items():
                est=method.update(obs)
                if frame in truth:
                    error=(abs(math.degrees(wrap_angle(est.theta-truth[frame])))
                           if est.theta is not None else None)
                    results.append({'frame':frame,'time_s':obs.timestamp,'method':name,
                                    'status':est.status,'theta_rad':est.theta,
                                    'ground_truth_rad':truth[frame],'abs_error_deg':error,
                                    'sigma_theta_rad':est.sigma_theta,
                                    'crank_visible':int('crank' in landmarks),
                                    'piston_visible':int('piston' in landmarks)})
    if not results:raise ValueError('No matched frame IDs in recording and ground truth')
    summary={}
    for name in methods:
        group=[r for r in results if r['method']==name]
        errors=np.array([r['abs_error_deg'] for r in group if r['abs_error_deg'] is not None],dtype=float)
        visible=[r for r in group if r['crank_visible']==0 and r['piston_visible']==1]
        summary[name]={
            'num_reference_frames':len(group),
            'num_estimates':len(errors),
            'coverage_pct':100*len(errors)/len(group),
            'mae_deg':float(errors.mean()) if len(errors) else None,
            'rmse_deg':float(np.sqrt(np.mean(errors**2))) if len(errors) else None,
            'p95_abs_error_deg':float(np.percentile(errors,95)) if len(errors) else None,
            'crank_occluded_piston_visible_coverage_pct':(
                100*sum(r['abs_error_deg'] is not None for r in visible)/len(visible)
                if visible else None),
        }
    # Paired differences over exactly the same frames that both methods estimate.
    method_errors={name:{r['frame']:r['abs_error_deg'] for r in results
                         if r['method']==name and r['abs_error_deg'] is not None}
                   for name in methods}
    pair=set(method_errors['physics_ekf']) & set(method_errors['temporal_ekf'])
    delta=np.array([method_errors['temporal_ekf'][i]-method_errors['physics_ekf'][i]
                    for i in sorted(pair)],dtype=float)
    result={'dataset':'REAL_REFERENCED_REPLAY','geometry_file':str(geometry_file),
            'session_file':str(session_file),'reference_file':str(ground_truth_file),
            'methods':summary,
            'paired_temporal_minus_physics_mae_deg':float(delta.mean()) if len(delta) else None,
            'paired_frame_count':len(delta),
            'notes':'Positive paired difference means physics EKF had lower absolute error on the paired frames. '
                    'Adjacent frames are correlated; evaluate significance across independent sessions.'}
    with (output/'real_ablation.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]))
        writer.writeheader();writer.writerows(results)
    (output/'real_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
