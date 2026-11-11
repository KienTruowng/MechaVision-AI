"""Thu nhận camera/video; dùng dấu thời gian tương đối cho video đã ghi."""
from __future__ import annotations
import time
import math
import cv2

class FrameSource:
    def __init__(self, source:int|str, width:int=960,height:int=540):
        self.source=source
        self.cap=cv2.VideoCapture(source)
        if not self.cap.isOpened():
            self.cap.release()
            raise RuntimeError(f'Không mở được nguồn camera/video: {source}')
        if isinstance(source,int):
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
        self.is_file=isinstance(source,str)
        self.t0=time.perf_counter()
        self.frame_id=0
        self.last_ts=0.0

    def read(self):
        ok,frame=self.cap.read()
        if not ok:
            if self.is_file:
                return None
            # Camera không có EOF: thử lại hữu hạn khi mất khung tạm thời.
            for _ in range(2):
                time.sleep(0.02)
                ok,frame=self.cap.read()
                if ok:break
            if not ok:
                raise RuntimeError('Mất khung hình camera sau 3 lần đọc; hãy kiểm tra kết nối và bắt đầu lại phiên.')
        self.frame_id+=1
        if self.is_file:
            ts=self.cap.get(cv2.CAP_PROP_POS_MSEC)/1000.0
            if not math.isfinite(ts) or ts<=self.last_ts:
                fps=self.cap.get(cv2.CAP_PROP_FPS)
                ts=(self.frame_id-1)/(fps if math.isfinite(fps) and fps>0 else 30)
        else:ts=time.perf_counter()-self.t0
        self.last_ts=max(self.last_ts+1e-6,ts)
        return frame,self.last_ts,self.frame_id

    def close(self):self.cap.release()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
