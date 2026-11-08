"""Công cụ chạy không cửa sổ/OpenCV: camera hoặc video → nhận diện → ước lượng trạng thái."""
from __future__ import annotations
from .i18n import put_text
import time
from pathlib import Path
import cv2
from .acquisition import FrameSource
from .geometry import Geometry
from .detection import make_detector,draw_observations
from .processing import Processor
from .render import decorate_video


def run_live(source:int|str,geometry_path:str,detector:str='color',weights:str|None=None,
             device:str='cpu',out:str='outputs/live.csv',show:bool=True,
             video_out:str|None=None):
    geo=Geometry.from_json(geometry_path)
    det=make_detector(detector,weights,device)
    writer=None
    if video_out:Path(video_out).parent.mkdir(parents=True,exist_ok=True)
    processor=Processor(geo,out)
    try:
        with FrameSource(source) as stream:
            while True:
                sample=stream.read()
                if sample is None:break
                frame,ts,i=sample
                obs=det.detect(frame,ts,i)
                metrics=processor.step(obs)
                est=metrics['physics']
                if show or video_out:
                    overlay=draw_observations(frame.copy(),obs)
                    decorate_video(overlay,est.status,metrics['fps'])
                    if est.theta is not None:
                        label=f'Góc {est.theta*180/3.14159265:.1f}° | Tốc độ {est.rpm:.1f} vòng/phút'
                        put_text(overlay,label,(15,69),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),2)
                    if writer is None and video_out:
                        fps=stream.cap.get(cv2.CAP_PROP_FPS)
                        if fps<1 or fps>180:fps=30
                        writer=cv2.VideoWriter(video_out,cv2.VideoWriter_fourcc(*'mp4v'),
                                               fps,(overlay.shape[1],overlay.shape[0]))
                        if not writer.isOpened():raise RuntimeError(f'Không ghi được video: {video_out}')
                    if writer:writer.write(overlay)
                    if show:
                        cv2.imshow('MechaVision AI — Đo từ camera/video | Nhấn Q để thoát',overlay)
                        if (cv2.waitKey(1)&0xff) in (27,ord('q')):break
    finally:
        processor.close()
        if writer:writer.release()
        if show:cv2.destroyAllWindows()
    return str(Path(out).resolve())
