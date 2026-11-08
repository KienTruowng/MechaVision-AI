"""Four-click physical joint geometry calibration from a static frame."""
from __future__ import annotations
import cv2
from .geometry import Geometry

LABELS=('Fixed pivot O','Crank pin C','Piston / connecting rod joint S','Positive slider axis direction')

def calibrate_interactively(source:int|str,output:str)->Geometry:
    cap=cv2.VideoCapture(source)
    if not cap.isOpened():raise RuntimeError(f'Cannot open source: {source}')
    try:
        ok,image=cap.read()
        if not ok:raise RuntimeError('No frame from source')
    finally:cap.release()
    pts=[]
    win='MechaVision - calibration (left click 4 points, r reset, ESC exit)'
    def on_mouse(event,x,y,flags,userdata):
        if event==cv2.EVENT_LBUTTONDOWN and len(pts)<4:pts.append((float(x),float(y)))
    cv2.namedWindow(win,cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win,on_mouse)
    try:
        while True:
            show=image.copy()
            for i,(x,y) in enumerate(pts):
                cv2.circle(show,(int(x),int(y)),6,(0,255,255),-1)
                cv2.putText(show,str(i+1),(int(x)+10,int(y)-10),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
            msg='Click '+LABELS[len(pts)] if len(pts)<4 else 'ENTER save / R reset'
            cv2.rectangle(show,(0,0),(show.shape[1],44),(20,25,35),-1)
            cv2.putText(show,msg,(10,30),cv2.FONT_HERSHEY_SIMPLEX,.65,(210,230,255),2)
            cv2.imshow(win,show)
            key=cv2.waitKey(30)&0xff
            if key in (27,ord('q')):raise RuntimeError('Calibration canceled')
            if key==ord('r'):pts.clear()
            if key in (10,13) and len(pts)==4:
                geo=Geometry.from_landmarks(*pts)
                geo.to_json(output)
                return geo
    finally:cv2.destroyWindow(win)
