"""Detection adapters. YOLO requires user-trained weights, never bundled/faked."""
from __future__ import annotations
import cv2
from .types import Observation,Landmark


class ArucoDetector:
    """Fiducial-based pilot measurement: ids 0 pivot, 1 crank, 2 piston.

    Place marker *centers* at the modeled landmarks; otherwise an offset
    calibration is mandatory. Pivot must be visible at least for calibration.
    """
    mapping={0:"pivot",1:"crank",2:"piston"}
    def __init__(self):
        if not hasattr(cv2,"aruco"):
            raise RuntimeError("Install opencv-contrib-python (not opencv-python).")
        aruco=cv2.aruco
        self.dictionary=aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.parameters=aruco.DetectorParameters()
        self.detector=aruco.ArucoDetector(self.dictionary,self.parameters)

    def detect(self,frame,timestamp,frame_id=0)->Observation:
        corners,ids,_=self.detector.detectMarkers(frame)
        points={}
        if ids is not None:
            for corner,marker_id in zip(corners,ids.reshape(-1)):
                name=self.mapping.get(int(marker_id))
                if name is None:continue
                center=corner.reshape(4,2).mean(axis=0)
                points[name]=Landmark(float(center[0]),float(center[1]),0.95)
        return Observation(timestamp,points,frame_id=frame_id)


class YOLOPoseDetector:
    """One mechanism per frame, three custom keypoints: pivot, crank, piston.

    This does not use stock human-pose weights. An explicitly trained pose
    checkpoint with the matching class and keypoint ordering is required.
    """
    def __init__(self,weights:str,confidence:float=0.35,device:str="cpu"):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError('Install optional dependencies: pip install -e ".[train]"') from exc
        self.model=YOLO(weights)
        self.confidence=confidence
        self.device=device

    def detect(self,frame,timestamp,frame_id=0)->Observation:
        results=self.model.predict(frame,conf=self.confidence,device=self.device,verbose=False)
        landmarks={}
        if results and results[0].keypoints is not None and len(results[0].keypoints)>0:
            k=results[0].keypoints
            xy=k.xy.cpu().numpy()
            scores=k.conf.cpu().numpy() if k.conf is not None else None
            # Select single highest-confidence mechanism detection
            boxes=results[0].boxes
            idx=int(boxes.conf.argmax().item()) if boxes is not None and len(boxes)>0 else 0
            for j,name in enumerate(("pivot","crank","piston")):
                if j>=xy.shape[1]:continue
                score=float(scores[idx,j]) if scores is not None else 1.0
                x,y=xy[idx,j]
                if score>=self.confidence and x>=0 and y>=0:
                    landmarks[name]=Landmark(float(x),float(y),score)
        return Observation(timestamp,landmarks,frame_id=frame_id)


def draw_observations(frame,obs:Observation):
    colors={"pivot":(230,230,230),"crank":(70,174,251),"piston":(81,230,164)}
    for name,p in obs.landmarks.items():
        q=(round(p.x),round(p.y))
        cv2.circle(frame,q,7,colors.get(name,(255,255,255)),2,cv2.LINE_AA)
        cv2.putText(frame,f"{name} {p.confidence:.2f}",(q[0]+12,q[1]-11),
                    cv2.FONT_HERSHEY_SIMPLEX,.47,colors.get(name,(255,255,255)),1,cv2.LINE_AA)
    return frame

class ColorMarkerDetector:
    """Practical untrained camera baseline for circular stickers.

    Red=pivot, green=crank pin, blue=actual piston/rod joint. Use saturated
    colored markers and diffuse lighting. Marker centers must coincide with
    modeled joints or be corrected by a physical offset calibration.
    """
    def __init__(self,min_area:float=30.0,max_area:float=7000.0):
        self.min_area=min_area
        self.max_area=max_area

    def detect(self,frame,timestamp,frame_id=0)->Observation:
        import numpy as np
        hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        ranges={
            'pivot':[((0,100,90),(10,255,255)),((170,100,90),(179,255,255))],
            'crank':[((35,80,75),(88,255,255))],
            'piston':[((90,90,75),(135,255,255))],
        }
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        pts={}
        for key,bands in ranges.items():
            mask=None
            for low,high in bands:
                sub=cv2.inRange(hsv,np.array(low,dtype=np.uint8),np.array(high,dtype=np.uint8))
                mask=sub if mask is None else cv2.bitwise_or(mask,sub)
            mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
            contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            accepted=[c for c in contours if self.min_area<=cv2.contourArea(c)<=self.max_area]
            if not accepted: continue
            c=max(accepted,key=cv2.contourArea)
            moments=cv2.moments(c)
            if abs(moments['m00'])<1e-8:continue
            area=cv2.contourArea(c)
            per=cv2.arcLength(c,True)
            circularity=4*np.pi*area/(per*per+1e-9)
            if circularity<0.35:continue
            conf=float(max(0.4,min(1.0,circularity)))
            pts[key]=Landmark(float(moments['m10']/moments['m00']),
                              float(moments['m01']/moments['m00']),conf)
        return Observation(timestamp,pts,frame_id=frame_id)


def make_detector(mode:str,weights:str|None=None,device:str='cpu'):
    if mode=='aruco':return ArucoDetector()
    if mode=='color':return ColorMarkerDetector()
    if mode=='yolo':
        if not weights:raise ValueError('YOLO detector requires trained --weights path')
        return YOLOPoseDetector(weights,device=device)
    raise ValueError(f'Unknown detection mode: {mode}')


def create_aruco_sheet(path:str,marker_size:int=300):
    """Create printable marker sheet, ids 0 (pivot), 1 (crank), 2 (piston)."""
    import numpy as np
    if not hasattr(cv2,'aruco'):
        raise RuntimeError('opencv-contrib-python required')
    aruco=cv2.aruco
    dictionary=aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    cell=marker_size+90
    image=np.full((cell,3*cell,3),255,dtype=np.uint8)
    for i,name in enumerate(('PIVOT 0','CRANK 1','PISTON 2')):
        marker=aruco.generateImageMarker(dictionary,i,marker_size)
        x=i*cell+45
        image[38:38+marker_size,x:x+marker_size]=cv2.cvtColor(marker,cv2.COLOR_GRAY2BGR)
        cv2.putText(image,name,(x,marker_size+65),cv2.FONT_HERSHEY_SIMPLEX,.85,(0,0,0),2)
    from pathlib import Path
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if not cv2.imwrite(str(p),image):raise OSError(f'Could not write {p}')
    return p
