"""Ghi các phiên camera độc lập để gán nhãn điểm đặc trưng."""
from __future__ import annotations
from .i18n import put_text
from pathlib import Path
import time
import cv2

def record_camera(camera:int,out:str,seconds:float=20.0):
    if seconds<=0:raise ValueError('seconds phải dương')
    target=Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(camera)
    if not cap.isOpened():raise RuntimeError(f'Không mở được camera {camera}')
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,960);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,540)
    writer=None;start=time.perf_counter();count=0
    try:
        while time.perf_counter()-start<seconds:
            ok,frame=cap.read()
            if not ok:break
            if writer is None:
                height,width=frame.shape[:2]
                writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'mp4v'),30.0,(width,height))
                if not writer.isOpened():raise RuntimeError(f'Không tạo được video đầu ra: {target}')
            writer.write(frame);count+=1
            put_text(frame,'GHI HÌNH GỐC — NHẤN Q ĐỂ DỪNG',(10,29),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),2)
            cv2.imshow('MechaVision — Ghi hình gốc',frame)
            if cv2.waitKey(1)&0xff in (27,ord('q')):break
    finally:
        cap.release()
        if writer:writer.release()
        cv2.destroyAllWindows()
    if count==0:raise RuntimeError('Không thu được khung hình camera')
    return target
