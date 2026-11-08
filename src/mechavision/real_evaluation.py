"""Đối chiếu ước lượng camera với góc tham chiếu ĐỘC LẬP theo mã khung hình.

CSV tham chiếu: frame,theta_deg (hoặc frame,theta_rad).
Không tạo nhãn bằng chính bộ ước lượng đang được đánh giá.
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import numpy as np
from .geometry import wrap_angle


def evaluate_recording(session_file:str,ground_truth_file:str,out:str|None=None):
    with open(ground_truth_file,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or 'frame' not in reader.fieldnames or not ({'theta_deg','theta_rad'}&set(reader.fieldnames)):
            raise ValueError('Dữ liệu tham chiếu cần frame,theta_deg HOẶC frame,theta_rad')
        ground={}
        for row in reader:
            if not row['frame']:continue
            angle=(math.radians(float(row['theta_deg'])) if row.get('theta_deg') not in ('',None)
                   else float(row['theta_rad']))
            ground[int(row['frame'])]=angle
    with open(session_file,encoding='utf-8-sig',newline='') as f:
        session=list(csv.DictReader(f))
    aligned=[]
    for row in session:
        frame=int(row['frame'])
        if frame not in ground:continue
        angle=float(row['theta_rad']) if row.get('theta_rad') not in ('',None) else None
        error=abs(math.degrees(wrap_angle(angle-ground[frame]))) if angle is not None else None
        aligned.append({'frame':frame,'status':row.get('status'),'estimate_rad':angle,
                        'ground_truth_rad':ground[frame],'abs_error_deg':error})
    if not aligned:raise ValueError('Không có mã khung hình khớp giữa phiên đo và dữ liệu tham chiếu')
    values=np.array([r['abs_error_deg'] for r in aligned if r['abs_error_deg'] is not None],dtype=float)
    report={'dataset':'INDEPENDENT_REAL_GROUND_TRUTH','num_reference_frames':len(aligned),
            'num_estimates':len(values),'coverage_pct':100*len(values)/len(aligned),
            'mae_deg':float(values.mean()) if len(values) else None,
            'rmse_deg':float(np.sqrt(np.mean(values*values))) if len(values) else None,
            'p95_abs_error_deg':float(np.percentile(values,95)) if len(values) else None,
            'limitations':'Độ chính xác chỉ áp dụng cho khung hình có nhãn; vẫn có sai số camera và người gán nhãn.'}
    if out:
        path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return report


def evaluate_keypoints(dataset_dir:str,mode:str='yolo',weights:str|None=None,
                       split:str='test',device:str='cpu',threshold_px:float=10):
    """Sai số điểm so với nhãn thủ công của tập giữ lại, có thống kê tỷ lệ bỏ sót."""
    import cv2
    from .detection import make_detector
    from .dataset import KEYPOINT_NAMES
    base=Path(dataset_dir)
    images=sorted([*(base/'images'/split).glob('*.jpg'),*(base/'images'/split).glob('*.png')])
    if not images:raise ValueError(f'Không có ảnh trong {base/"images"/split}')
    detector=make_detector(mode,weights,device)
    errs=[];per={k:[] for k in KEYPOINT_NAMES};total=found=0
    for i,img in enumerate(images):
        frame=cv2.imread(str(img))
        if frame is None:continue
        h,w=frame.shape[:2]
        target=base/'labels'/split/(img.stem+'.txt')
        if not target.exists():continue
        raw=target.read_text(encoding='utf-8').strip().split()
        if len(raw)!=14:raise ValueError(f'Nhãn điểm đặc trưng không hợp lệ {target}')
        obs=detector.detect(frame,float(i),i)
        for j,name in enumerate(KEYPOINT_NAMES):
            x,y,v=map(float,raw[5+j*3:8+j*3])
            if not v:continue
            total+=1
            if name not in obs.landmarks:continue
            found+=1;p=obs.landmarks[name]
            d=float(np.hypot(p.x-x*w,p.y-y*h));errs.append(d);per[name].append(d)
    return {'dataset':'HELD_OUT_MANUAL_ANNOTATIONS','num_images':len(images),
            'visible_reference_points':total,'detected_points':found,
            'recall':found/total if total else None,
            'mae_px':float(np.mean(errs)) if errs else None,
            'rmse_px':float(np.sqrt(np.mean(np.asarray(errs)**2))) if errs else None,
            'pck_at_threshold':float(np.mean(np.asarray(errs)<=threshold_px)) if errs else None,
            'threshold_px':threshold_px,
            'per_keypoint_mae_px':{k:float(np.mean(v)) if v else None for k,v in per.items()},
            'note':'Điểm bỏ sót được tính trong recall; PCK chỉ tính trên điểm đã phát hiện.'}
