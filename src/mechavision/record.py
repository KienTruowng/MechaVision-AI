"""Record short physically independent camera sessions for pose labeling."""
from __future__ import annotations
from pathlib import Path
import time
import cv2

def record_camera(camera:int,out:str,seconds:float=20.0):
    if seconds<=0:raise ValueError('seconds must be positive')
    target=Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(camera)
    if not cap.isOpened():raise RuntimeError(f'Cannot open camera {camera}')
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,960);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,540)
    writer=None;start=time.perf_counter();count=0
    try:
        while time.perf_counter()-start<seconds:
            ok,frame=cap.read()
            if not ok:break
            if writer is None:
                height,width=frame.shape[:2]
                writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'mp4v'),30.0,(width,height))
                if not writer.isOpened():raise RuntimeError(f'Cannot create output video: {target}')
            writer.write(frame);count+=1
            cv2.putText(frame,'RAW CAPTURE - PRESS Q TO STOP',(10,29),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),2)
            cv2.imshow('MechaVision Raw Capture',frame)
            if cv2.waitKey(1)&0xff in (27,ord('q')):break
    finally:
        cap.release()
        if writer:writer.release()
        cv2.destroyAllWindows()
    if count==0:raise RuntimeError('No camera frames captured')
    return target
