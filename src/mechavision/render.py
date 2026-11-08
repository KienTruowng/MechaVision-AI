"""Lớp phủ hiển thị phép đo và giá trị ước lượng."""
from .i18n import put_text, status_text
import cv2
import math
from .types import Estimate


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
    import numpy as np
    img=np.full((height,width,3),(31,19,7),dtype=np.uint8)
    for x in range(20,width,40):cv2.line(img,(x,65),(x,height-50),(44,31,17),1)
    for y in range(65,height-40,40):cv2.line(img,(20,y),(width-20,y),(44,31,17),1)
    put_text(img,f'r = {geo.radius_px:.1f} px   l = {geo.rod_px:.1f} px   e = {geo.slider_offset_px:.1f} px',
             (22,28),cv2.FONT_HERSHEY_SIMPLEX,.48,(181,158,128),1,cv2.LINE_AA)
    label='Chưa có trạng thái' if est is None else status_text(est.status)
    color=(177,213,72) if est is not None and est.status=='TRACKING' else (106,195,240)
    put_text(img,label,(22,52),cv2.FONT_HERSHEY_SIMPLEX,.53,color,1,cv2.LINE_AA)
    if est is None or est.theta is None:
        put_text(img,'KHÔNG ĐỦ ĐỘ TIN CẬY ĐỂ ƯỚC LƯỢNG',(60,height//2),
                    cv2.FONT_HERSHEY_SIMPLEX,.58,(124,140,163),1,cv2.LINE_AA)
        return img
    scale=min((width-130)/(geo.rod_px+2*geo.radius_px),
              (height-155)/(2*geo.radius_px+abs(geo.slider_offset_px)))
    pivot=np.array([35+geo.radius_px*scale,height*.53],dtype=float)
    def xy(pos):return tuple(np.rint(pivot+np.array([pos[0],-pos[1]])*scale).astype(int))
    r=geo.radius_px
    O=xy((0,0));C=xy((r*np.cos(est.theta),r*np.sin(est.theta)))
    P=xy((geo.slider_x(est.theta),geo.slider_offset_px))
    cv2.arrowedLine(img,(30,O[1]),(width-26,O[1]),(91,66,41),1,tipLength=.025)
    cv2.arrowedLine(img,(O[0],height-65),(O[0],80),(91,66,41),1,tipLength=.04)
    for offset in (-25,25):cv2.line(img,(max(30,P[0]-80),P[1]+offset),(width-35,P[1]+offset),(97,76,49),2)
    cv2.circle(img,O,int(r*scale),(95,65,37),1,cv2.LINE_AA)
    cv2.line(img,O,C,(255,143,67),8,cv2.LINE_AA)
    cv2.line(img,C,P,(237,212,80),7,cv2.LINE_AA)
    cv2.rectangle(img,(P[0]-17,P[1]-21),(P[0]+17,P[1]+21),(104,73,34),-1)
    cv2.rectangle(img,(P[0]-17,P[1]-21),(P[0]+17,P[1]+21),(237,212,80),2)
    for name,pt in (('O',O),('C',C),('S',P)):
        cv2.circle(img,pt,7,(35,20,8),-1,cv2.LINE_AA)
        cv2.circle(img,pt,7,(237,219,191),2,cv2.LINE_AA)
        put_text(img,name,(pt[0]+11,pt[1]-13),cv2.FONT_HERSHEY_SIMPLEX,.47,(220,203,179),1)
    put_text(img,'x',(width-22,O[1]-8),cv2.FONT_HERSHEY_SIMPLEX,.45,(161,130,94),1)
    put_text(img,'y',(O[0]+9,82),cv2.FONT_HERSHEY_SIMPLEX,.45,(161,130,94),1)
    put_text(img,f'Góc ước lượng: {math.degrees(est.theta):.1f}°',(22,height-23),
             cv2.FONT_HERSHEY_SIMPLEX,.51,(214,190,160),1,cv2.LINE_AA)
    return img


def decorate_video(frame,status,fps):
    cv2.rectangle(frame,(0,0),(frame.shape[1],45),(46,29,20),-1)
    color={'TRACKING':(177,213,72),'PREDICTED':(106,195,240),'LOST':(135,123,255)}.get(status,(177,177,177))
    put_text(frame,f'{status_text(status)}  |  {fps:.1f} khung/giây xử lý',(15,29),
                cv2.FONT_HERSHEY_SIMPLEX,.61,color,2,cv2.LINE_AA)
    return frame
