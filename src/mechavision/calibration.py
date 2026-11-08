"""Hiệu chuẩn hình học khớp bằng bốn lần nhấp trên một khung hình tĩnh."""
from __future__ import annotations
from .i18n import put_text
import cv2
from .geometry import Geometry

LABELS=('Tâm quay cố định O','Chốt khuỷu C','Khớp pít-tông–thanh truyền S','Chiều dương trục trượt')

def calibrate_interactively(source:int|str,output:str)->Geometry:
    cap=cv2.VideoCapture(source)
    if not cap.isOpened():raise RuntimeError(f'Không mở được nguồn: {source}')
    try:
        ok,image=cap.read()
        if not ok:raise RuntimeError('Nguồn không cung cấp khung hình')
    finally:cap.release()
    pts=[]
    win='MechaVision — Hiệu chuẩn: nhấp 4 điểm, R đặt lại, Esc thoát'
    def on_mouse(event,x,y,flags,userdata):
        if event==cv2.EVENT_LBUTTONDOWN and len(pts)<4:pts.append((float(x),float(y)))
    cv2.namedWindow(win,cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win,on_mouse)
    try:
        while True:
            show=image.copy()
            for i,(x,y) in enumerate(pts):
                cv2.circle(show,(int(x),int(y)),6,(0,255,255),-1)
                put_text(show,str(i+1),(int(x)+10,int(y)-10),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
            msg='Nhấp chọn '+LABELS[len(pts)] if len(pts)<4 else 'Enter: lưu / R: đặt lại'
            cv2.rectangle(show,(0,0),(show.shape[1],44),(20,25,35),-1)
            put_text(show,msg,(10,30),cv2.FONT_HERSHEY_SIMPLEX,.65,(210,230,255),2)
            cv2.imshow(win,show)
            key=cv2.waitKey(30)&0xff
            if key in (27,ord('q')):raise RuntimeError('Đã hủy hiệu chuẩn')
            if key==ord('r'):pts.clear()
            if key in (10,13) and len(pts)==4:
                geo=Geometry.from_landmarks(*pts)
                geo.to_json(output)
                return geo
    finally:cv2.destroyWindow(win)
