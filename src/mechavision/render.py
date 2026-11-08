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


def twin_frame(geo,est,width=620,height=390):
    """Bản vẽ cơ khí theo ước lượng; phép biến đổi hiển thị luôn đồng tỷ lệ."""
    import numpy as np
    img=np.full((height,width,3),(31,19,7),dtype=np.uint8)
    compact=height<270
    top=34 if compact else 64
    bottom=height-30
    for x in range(24,width,48):
        cv2.line(img,(x,top),(x,bottom),(43,30,17),1)
    for y in range(top,bottom,48):
        cv2.line(img,(24,y),(width-24,y),(43,30,17),1)
    put_text(img,f'r {geo.radius_px:.0f} px   /   l {geo.rod_px:.0f} px   /   e {geo.slider_offset_px:.0f} px',
             (18,21),fontScale=.45 if compact else .52,color=(196,176,150))
    label='Chưa có trạng thái' if est is None else status_text(est.status)
    color={'TRACKING':(177,213,72),'PREDICTED':(106,195,240),'LOST':(135,123,255)}.get(
        est.status if est is not None else 'UNINITIALIZED',(161,137,112))
    put_text(img,label,(max(18,width-145),21) if compact else (18,46),
             fontScale=.45 if compact else .54,color=color)
    if est is None or est.theta is None or est.status not in ('TRACKING','PREDICTED'):
        put_text(img,'Không đủ độ tin cậy để dựng cơ cấu',(24,height//2+10),
                 fontScale=.62,color=(163,140,124))
        return img
    # Miền toàn vòng cố định: không phóng to/thu nhỏ theo góc hoặc thời gian.
    r=geo.radius_px
    ymin=min(-r,geo.slider_offset_px)
    ymax=max(r,geo.slider_offset_px)
    xmin=-r
    xmax=geo.rod_px+r
    scale=min((width-96)/(xmax-xmin),(bottom-top-44)/(ymax-ymin))
    scale=max(.01,scale)
    center=np.array([width/2,(top+bottom)/2],dtype=float)
    midpoint=np.array([(xmin+xmax)/2,(ymin+ymax)/2])
    def xy(pos):
        delta=(np.array(pos)-midpoint)*scale
        return tuple(np.rint(center+delta*np.array([1,-1])).astype(int))
    O=xy((0,0));C=xy((r*np.cos(est.theta),r*np.sin(est.theta)))
    P=xy((geo.slider_x(est.theta),geo.slider_offset_px))
    axis=(93,69,43); blue=(255,143,67); cyan=(237,212,80)
    cv2.arrowedLine(img,(22,O[1]),(width-22,O[1]),axis,1,tipLength=.02)
    cv2.arrowedLine(img,(O[0],bottom),(O[0],top),axis,1,tipLength=.04)
    cv2.circle(img,O,max(1,round(r*scale)),(87,62,35),1,cv2.LINE_AA)
    # Ray dẫn hướng giữ nguyên trục lệch tâm của mô hình.
    rail_start=max(24,xy((geo.rod_px-r,geo.slider_offset_px))[0]-30)
    for offset in (-22,22):
        cv2.line(img,(rail_start,P[1]+offset),(width-24,P[1]+offset),(129,100,65),3,cv2.LINE_AA)
        cv2.line(img,(rail_start,P[1]+offset+4),(width-24,P[1]+offset+4),(59,44,27),1)
    # Bệ ổ trục, vành đỡ và hai thanh có biên rõ trên nền graphite.
    cv2.rectangle(img,(O[0]-18,O[1]+16),(O[0]+18,O[1]+23),(105,82,53),-1)
    cv2.circle(img,O,19,(102,78,48),2,cv2.LINE_AA)
    cv2.circle(img,O,14,(54,38,22),-1,cv2.LINE_AA)
    for a,b,color,thickness in ((O,C,blue,13),(C,P,cyan,11)):
        cv2.line(img,a,b,(55,37,18),thickness+6,cv2.LINE_AA)
        cv2.line(img,a,b,color,thickness,cv2.LINE_AA)
        cv2.line(img,a,b,(218,209,187),2,cv2.LINE_AA)
    cv2.rectangle(img,(P[0]-22,P[1]-18),(P[0]+22,P[1]+18),(97,71,36),-1)
    cv2.rectangle(img,(P[0]-22,P[1]-18),(P[0]+22,P[1]+18),cyan,2)
    for dx in (-15,15):
        cv2.line(img,(P[0]+dx,P[1]-14),(P[0]+dx,P[1]+14),(168,138,83),2)
    for name,pt in (('O',O),('C',C),('S',P)):
        cv2.circle(img,pt,10,(52,34,17),-1,cv2.LINE_AA)
        cv2.circle(img,pt,7,(35,20,8),-1,cv2.LINE_AA)
        cv2.circle(img,pt,7,(237,219,191),2,cv2.LINE_AA)
        cv2.circle(img,pt,2,(220,207,183),-1,cv2.LINE_AA)
        put_text(img,name,(pt[0]+12,pt[1]-23),fontScale=.52,color=(231,215,190))
    put_text(img,'x',(width-22,O[1]-8),fontScale=.45,color=(161,130,94))
    put_text(img,'y',(O[0]+8,top+4),fontScale=.45,color=(161,130,94))
    cv2.line(img,(18,height-33),(width-18,height-33),(66,47,28),1)
    put_text(img,f'θ = {math.degrees(est.theta):.1f}°   ·   Cùng trạng thái ước lượng',
             (18,height-12),fontScale=.52,color=(221,205,180))
    return img


def decorate_video(frame,status,fps):
    cv2.rectangle(frame,(0,0),(frame.shape[1],45),(46,29,20),-1)
    color={'TRACKING':(177,213,72),'PREDICTED':(106,195,240),'LOST':(135,123,255)}.get(status,(177,177,177))
    put_text(frame,f'{status_text(status)}  |  {fps:.1f} khung/giây xử lý',(15,29),
                cv2.FONT_HERSHEY_SIMPLEX,.61,color,2,cv2.LINE_AA)
    return frame
