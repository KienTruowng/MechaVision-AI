"""Lớp phủ hiển thị phép đo và giá trị ước lượng."""
from .i18n import put_text, status_text, KEYPOINT_LABELS, _font
import cv2
import math
from .types import Estimate


def observation_label_layout(frame_shape,obs):
    """Đặt nhãn tránh chồng nhau/che tâm khớp; chỉ thay tọa độ chữ trên ảnh."""
    height,width=frame_shape[:2]
    placed=[]
    font=_font(21)
    points=[(round(point.x),round(point.y)) for point in obs.landmarks.values()]
    for name,point in obs.landmarks.items():
        text=f'{KEYPOINT_LABELS.get(name,name)} · {point.confidence:.2f}'
        bounds=font.getbbox(text)
        w=min(width-10,bounds[2]-bounds[0]);h=bounds[3]-bounds[1]
        x,y=round(point.x),round(point.y)
        candidates=[(-w-14,-20),(14,36),(14,-20),(-w-14,36),(-w//2,-50),(-w//2,65)]
        if name=='crank':candidates=candidates[1:]+candidates[:1]
        if name=='piston':candidates=candidates[2:]+candidates[:2]
        choices=[]
        for dx,dy in candidates:
            left=max(5,min(width-w-5,x+dx))
            baseline=max(50+h,min(height-38,y+dy))
            box=(left,baseline-h,left+w,baseline)
            overlap=sum(max(0,min(box[2],previous[2])-max(box[0],previous[0]))*
                        max(0,min(box[3],previous[3])-max(box[1],previous[1]))
                        for _,_,previous in placed)
            covered=sum(box[0]-9<px<box[2]+9 and box[1]-9<py<box[3]+9 for px,py in points)
            score=overlap*100+covered*100000+abs(dx)+abs(dy)
            choices.append((score,box))
        _,box=min(choices,key=lambda candidate:candidate[0])
        placed.append((name,text,box))
    return placed


def draw_observation_labels(frame,obs,colors):
    for name,text,box in observation_label_layout(frame.shape,obs):
        left,top,right,bottom=box
        cv2.rectangle(frame,(left-3,top-3),(right+3,bottom+3),(39,26,14),-1)
        put_text(frame,text,(left,bottom),cv2.FONT_HERSHEY_SIMPLEX,.75,
                 colors.get(name,(255,255,255)),1,cv2.LINE_AA)
    return frame


def draw_estimate(frame,estimate:Estimate):
    color={'TRACKING':(103,215,145),'PREDICTED':(60,190,229),'LOST':(88,88,235)}.get(estimate.status,(140,160,185))
    cv2.rectangle(frame,(8,8),(min(frame.shape[1]-8,360),95),(18,25,34),-1)
    put_text(frame,status_text(estimate.status),(18,34),cv2.FONT_HERSHEY_SIMPLEX,.68,color,2,cv2.LINE_AA)
    if estimate.theta is not None:
        put_text(frame,f'Góc: {math.degrees(estimate.theta)%360:.1f}°',(18,59),cv2.FONT_HERSHEY_SIMPLEX,.54,(232,236,245),1,cv2.LINE_AA)
    if estimate.rpm is not None:
        put_text(frame,f'Tốc độ: {estimate.rpm:.1f} vòng/phút',(18,81),cv2.FONT_HERSHEY_SIMPLEX,.53,(232,236,245),1,cv2.LINE_AA)
    return frame


def twin_frame(geo, est, width=620, height=390):
    from .twin_renderer import render_twin

    return render_twin(geo, est, width, height)


def decorate_video(frame,status,fps):
    cv2.rectangle(frame,(0,0),(frame.shape[1],45),(46,29,20),-1)
    color={'TRACKING':(177,213,72),'PREDICTED':(106,195,240),'LOST':(135,123,255)}.get(status,(177,177,177))
    put_text(frame,f'{status_text(status)}  |  {fps:.1f} khung/giây xử lý',(15,29),
                cv2.FONT_HERSHEY_SIMPLEX,.61,color,2,cv2.LINE_AA)
    return frame
