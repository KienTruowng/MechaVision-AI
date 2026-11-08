"""Huấn luyện và đánh giá YOLO Pose thực sự; không tạo trọng số giả."""
from __future__ import annotations
from pathlib import Path


def train_pose(dataset_yaml:str,model:str='yolo11n-pose.pt',epochs:int=80,
               imgsz:int=640,batch:int=8,device:str|None=None):
    if not Path(dataset_yaml).is_file():raise FileNotFoundError(dataset_yaml)
    from ultralytics import YOLO
    net=YOLO(model)
    kwargs=dict(data=dataset_yaml,epochs=epochs,imgsz=imgsz,batch=batch,
                project='runs/mechavision',name='pose',exist_ok=False,
                seed=42,patience=20,plots=True)
    if device is not None:kwargs['device']=device
    result=net.train(**kwargs)
    return result


def validate_pose(weights:str,dataset_yaml:str,split:str='test',device:str|None=None):
    if not Path(weights).is_file():raise FileNotFoundError(weights)
    if split not in ('val','test'):raise ValueError('split phải là val hoặc test')
    from ultralytics import YOLO
    kwargs=dict(data=dataset_yaml,split=split,plots=True,project='runs/mechavision',name='validation')
    if device is not None:kwargs['device']=device
    return YOLO(weights).val(**kwargs)
