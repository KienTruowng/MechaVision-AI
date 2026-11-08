"""Dataset tools for custom single-mechanism, three-keypoint YOLO pose.

Landmark order: fixed pivot, rotating crank pin, piston rod joint.
Labels are human clicks and are not estimated by the physics algorithm.
Assign whole recording sessions to train or val; NEVER shuffle adjacent frames.
"""
from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np

KEYPOINT_NAMES=('pivot','crank','piston')


def yolo_pose_line(points:list[tuple[int,int]|None],width:int,height:int,padding:float=.08)->str:
    if len(points)!=3:raise ValueError('Exactly three keypoints required')
    if width<=0 or height<=0:raise ValueError('Image dimensions must be positive')
    visible=[(float(x),float(y)) for v in points if v is not None for x,y in [v]]
    if not visible:raise ValueError('At least one visible keypoint is required')
    xs=[x for x,_ in visible];ys=[y for _,y in visible]
    x0=min(xs);x1=max(xs);y0=min(ys);y1=max(ys)
    padx=max(15.,(x1-x0)*padding);pady=max(15.,(y1-y0)*padding)
    x0=max(0.,x0-padx);x1=min(width-1.,x1+padx)
    y0=max(0.,y0-pady);y1=min(height-1.,y1+pady)
    cx=(x0+x1)/(2*width);cy=(y0+y1)/(2*height)
    bw=max((x1-x0)/width,1/width);bh=max((y1-y0)/height,1/height)
    tokens=['0',f'{cx:.6f}',f'{cy:.6f}',f'{bw:.6f}',f'{bh:.6f}']
    for p in points:
        if p is None:tokens.extend(['0.000000','0.000000','0'])
        else:
            x,y=p
            if not 0<=x<width or not 0<=y<height:raise ValueError('Clicked point outside image')
            tokens.extend([f'{x/width:.6f}',f'{y/height:.6f}','2'])
    return ' '.join(tokens)+'\n'


def initialize_dataset(root:str|Path)->Path:
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    for split in ('train','val'):
        for folder in ('images','labels'):(root/folder/split).mkdir(parents=True,exist_ok=True)
    yaml=(f"path: {root.resolve().as_posix()}\n"
          "train: images/train\nval: images/val\n"
          "kpt_shape: [3, 3]\nflip_idx: [0, 1, 2]\n"
          "names:\n  0: slider_crank_mechanism\n")
    (root/'dataset.yaml').write_text(yaml,encoding='utf-8')
    (root/'ANNOTATION_GUIDE.md').write_text(
        '# Landmark protocol\n\n'
        '0 pivot: physical crank rotation center; 1 crank: physical crank pin center; '
        '2 piston: joint between connecting rod and slider.\n\n'
        'Click only physically visible joint centers. Leave occluded points missing. '
        'A marker center displaced from the real joint requires a geometric offset model; '
        'the current estimator assumes coincidence.\n\n'
        'Separate **recording sessions** between train and val to avoid temporal leakage. '
        'Use a separate test session never used for training or tuning.\n',encoding='utf-8')
    return root/'dataset.yaml'


def annotate_video(video:str,root:str,split:str='train',session:str='session01',stride:int=10):
    """OpenCV interactive click-label-save loop.

    Left click sets the next landmark in pivot/crank/piston order. 1/2/3 select
    the landmark explicitly; right click clears selected landmark. S saves,
    N skips, Q quits. Skipped frames never produce inferred labels.
    """
    if split not in ('train','val'):raise ValueError('split must be train or val')
    if not session or any(x in session for x in '/\\..'):raise ValueError('Use simple session ID without paths')
    if stride<1:raise ValueError('stride >= 1 required')
    initialize_dataset(root)
    cap=cv2.VideoCapture(video)
    if not cap.isOpened():raise RuntimeError('Cannot open video: '+str(video))
    window='MechaVision labeler | 1/2/3 select | L-click assign | R-click clear | S save | N next | Q quit'
    cv2.namedWindow(window,cv2.WINDOW_NORMAL)
    points=[None,None,None];selected=[0]
    def mouse(event,x,y,flags,data):
        if event==cv2.EVENT_LBUTTONDOWN:
            points[selected[0]]=(x,y)
            if selected[0]<2:selected[0]+=1
        elif event==cv2.EVENT_RBUTTONDOWN:points[selected[0]]=None
    cv2.setMouseCallback(window,mouse)
    saved=0;frame_idx=0
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            frame_idx+=1
            if frame_idx%stride:continue
            points[:]=[None,None,None];selected[0]=0
            while True:
                display=frame.copy()
                for i,p in enumerate(points):
                    if p is not None:
                        cv2.circle(display,p,6,(69,215,115),-1)
                        cv2.putText(display,f'{i+1}:{KEYPOINT_NAMES[i]}',(p[0]+9,p[1]-8),
                                    cv2.FONT_HERSHEY_SIMPLEX,.55,(200,255,220),2)
                cv2.rectangle(display,(0,0),(min(920,display.shape[1]),72),(19,25,36),-1)
                cv2.putText(display,f'Frame {frame_idx} | Selected {selected[0]+1}:{KEYPOINT_NAMES[selected[0]]}',
                            (12,25),cv2.FONT_HERSHEY_SIMPLEX,.59,(235,241,247),2)
                cv2.putText(display,'1 2 3: select  |  L-click: mark  |  R-click: clear  |  S: save  N: skip  Q: quit',
                            (12,52),cv2.FONT_HERSHEY_SIMPLEX,.49,(168,195,235),1)
                cv2.imshow(window,display)
                key=cv2.waitKey(30)&0xff
                if key in (ord('1'),ord('2'),ord('3')):selected[0]=key-ord('1')
                if key==ord('n'):break
                if key in (ord('q'),27):return saved
                if key==ord('s'):
                    if not any(p is not None for p in points):continue
                    h,w=frame.shape[:2];stem=f'{session}_f{frame_idx:07d}'
                    img=Path(root)/'images'/split/(stem+'.jpg')
                    lbl=Path(root)/'labels'/split/(stem+'.txt')
                    if not cv2.imwrite(str(img),frame):raise RuntimeError('Failed to write '+str(img))
                    lbl.write_text(yolo_pose_line(points,w,h),encoding='utf-8')
                    saved+=1;break
    finally:
        cap.release();cv2.destroyWindow(window)
    return saved


def generate_markers(out:str,size:int=240):
    if not hasattr(cv2,'aruco'):raise RuntimeError('Requires opencv-contrib-python')
    a=cv2.aruco;dictionary=a.getPredefinedDictionary(a.DICT_4X4_50)
    page=np.full((size+110,size*3+80,3),255,dtype=np.uint8)
    for i,name in enumerate(KEYPOINT_NAMES):
        marker=a.generateImageMarker(dictionary,i,size-30)
        x=30+i*size;y=20
        page[y:y+size-30,x:x+size-30]=cv2.cvtColor(marker,cv2.COLOR_GRAY2BGR)
        cv2.putText(page,f'ID {i}: {name}',(x,y+size+12),cv2.FONT_HERSHEY_SIMPLEX,.57,(0,0,0),2)
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
    if not cv2.imwrite(str(p),page):raise RuntimeError('Cannot save markers')
    return p


def train(dataset_yaml:str,model:str='yolo11n-pose.pt',epochs:int=80,imgsz:int=640,
          batch:int=8,device:str='0'):
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError('Install optional training libraries with pip install -e ".[train]"') from exc
    if not Path(dataset_yaml).is_file():raise FileNotFoundError(dataset_yaml)
    if epochs<1:raise ValueError('epochs must be positive')
    net=YOLO(model)
    return net.train(data=str(Path(dataset_yaml).resolve()),epochs=epochs,imgsz=imgsz,
                     batch=batch,device=device,project='runs/mechavision',name='keypoint',exist_ok=False)

# --- Reproducible three-way, session-level dataset pipeline ---
import json
import random
import shutil
KEYPOINTS=KEYPOINT_NAMES


def _label_line(points,size):
    return yolo_pose_line(points,int(size[0]),int(size[1]))


def extract_frames(video:str,session:str,root:str='data/labeled',stride:int=8,limit:int=1000):
    if not session or any(x in session for x in '/\\..'):
        raise ValueError('Session must be an unqualified simple name')
    if stride<=0 or limit<=0:raise ValueError('stride and limit must be positive')
    out=Path(root)/session;out.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(video)
    if not cap.isOpened():raise RuntimeError(f'Cannot open video: {video}')
    i=n=0
    try:
        while n<limit:
            ok,frame=cap.read()
            if not ok:break
            if i%stride==0:
                path=out/f'{i:07d}.jpg'
                if not cv2.imwrite(str(path),frame):raise OSError(f'Cannot save {path}')
                n+=1
            i+=1
    finally:cap.release()
    return n


def annotate_folder(session_folder:str):
    """3-keypoint click labeler. Left click joint, S skip missing, R reset,
    ENTER save and next image, Q quit. Images retain session provenance.
    """
    folder=Path(session_folder)
    images=sorted([*folder.glob('*.jpg'),*folder.glob('*.png')])
    if not images:raise ValueError(f'No images found in {folder}')
    window='MechaVision: click joint | S missing | R reset | ENTER save | Q exit'
    cv2.namedWindow(window,cv2.WINDOW_NORMAL)
    try:
        for image_file in images:
            target=image_file.with_suffix('.txt')
            if target.exists():continue
            frame=cv2.imread(str(image_file))
            if frame is None:continue
            pts=[]
            def mouse(event,x,y,flags,userdata):
                if event==cv2.EVENT_LBUTTONDOWN and len(pts)<3:pts.append((x,y))
            cv2.setMouseCallback(window,mouse)
            while True:
                display=frame.copy();h,w=display.shape[:2]
                for i,p in enumerate(pts):
                    if p is not None:
                        cv2.circle(display,p,6,(80,215,140),-1)
                        cv2.putText(display,KEYPOINTS[i],(p[0]+10,p[1]-8),
                                    cv2.FONT_HERSHEY_SIMPLEX,.55,(80,215,140),2)
                text=(f'CLICK {KEYPOINTS[len(pts)]} (S if occluded)' if len(pts)<3
                      else 'ENTER to save / R reset')
                cv2.rectangle(display,(0,0),(w,40),(20,25,37),-1)
                cv2.putText(display,f'{image_file.name}: {text}',(8,26),cv2.FONT_HERSHEY_SIMPLEX,.5,(240,240,240),1)
                cv2.imshow(window,display)
                key=cv2.waitKey(30)&0xff
                if key in (ord('q'),27):return
                if key==ord('r'):pts.clear()
                if key==ord('s') and len(pts)<3:pts.append(None)
                if key in (10,13) and len(pts)==3:
                    if not any(p is not None for p in pts):pts.clear();continue
                    target.write_text(yolo_pose_line(pts,w,h),encoding='utf-8')
                    image_file.with_suffix('.json').write_text(json.dumps({'points':{
                        name:(None if p is None else list(p)) for name,p in zip(KEYPOINTS,pts)},
                        'width':w,'height':h},indent=2),encoding='utf-8')
                    break
    finally:cv2.destroyWindow(window)


def split_by_session(root:str='data/labeled',out:str='data/pose_dataset',seed:int=42):
    """Train/val/test cannot share frames from the same capture session."""
    base=Path(root)
    sessions=[d for d in sorted(base.iterdir()) if d.is_dir() and any(
        im.with_suffix('.txt').is_file() for im in [*d.glob('*.jpg'),*d.glob('*.png')])]
    if len(sessions)<3:raise ValueError('At least three labeled sessions required for train/val/test')
    rng=random.Random(seed);rng.shuffle(sessions)
    n=len(sessions);nt=max(1,round(n*.2));nv=max(1,round(n*.2))
    groups={'test':sessions[:nt],'val':sessions[nt:nt+nv],'train':sessions[nt+nv:]}
    dest=Path(out)
    if dest.exists():shutil.rmtree(dest)
    counts={}
    for split,folders in groups.items():
        (dest/'images'/split).mkdir(parents=True,exist_ok=True)
        (dest/'labels'/split).mkdir(parents=True,exist_ok=True)
        count=0
        for folder in folders:
            for img in sorted([*folder.glob('*.jpg'),*folder.glob('*.png')]):
                label=img.with_suffix('.txt')
                if not label.is_file():continue
                name=f'{folder.name}__{img.stem}'
                shutil.copy2(img,dest/'images'/split/(name+img.suffix))
                shutil.copy2(label,dest/'labels'/split/(name+'.txt'))
                count+=1
        counts[split]=count
    if any(v==0 for v in counts.values()):raise ValueError('Each split requires labeled images')
    (dest/'data.yaml').write_text(
        f'path: {dest.resolve().as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\n'
        'kpt_shape: [3, 3]\nflip_idx: [0, 1, 2]\nnames:\n  0: mechanism\n',encoding='utf-8')
    (dest/'split_manifest.json').write_text(json.dumps({
        'seed':seed,'sessions':{k:[s.name for s in v] for k,v in groups.items()},
        'image_counts':counts},indent=2),encoding='utf-8')
    return counts
