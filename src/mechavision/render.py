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
    img=np.full((height,width,3),(21,28,42),dtype=np.uint8)
    put_text(img,'MÔ HÌNH ĐỘNG HỌC SỐ / ƯỚC LƯỢNG',(22,32),
                cv2.FONT_HERSHEY_SIMPLEX,.56,(215,219,229),1,cv2.LINE_AA)
    if est is None or est.theta is None:
        put_text(img,'KHÔNG ĐỦ ĐỘ TIN CẬY ĐỂ ƯỚC LƯỢNG',(60,height//2),
                    cv2.FONT_HERSHEY_SIMPLEX,.65,(80,155,233),2,cv2.LINE_AA)
        return img
    scale=min((width-110)/(2*(geo.rod_px+geo.radius_px)),(height-110)/(3*geo.radius_px))
    pivot=np.array([max(95,width*.26),height*.53],dtype=float)
    def xy(pos):return tuple(np.rint(pivot+np.array([pos[0],-pos[1]])*scale).astype(int))
    r=geo.radius_px
    O=xy((0,0));C=xy((r*np.cos(est.theta),r*np.sin(est.theta)))
    P=xy((geo.slider_x(est.theta),geo.slider_offset_px))
    cv2.line(img,(25,O[1]),(width-20,O[1]),(55,73,93),2)
    cv2.circle(img,O,int(r*scale),(65,76,91),1,cv2.LINE_AA)
    cv2.line(img,O,C,(226,167,88),9,cv2.LINE_AA)
    cv2.line(img,C,P,(82,199,205),8,cv2.LINE_AA)
    cv2.rectangle(img,(P[0]-15,P[1]-23),(P[0]+15,P[1]+23),(70,136,215),-1)
    for pt in (O,C,P):cv2.circle(img,pt,6,(235,238,244),-1,cv2.LINE_AA)
    put_text(img,'HIỂN THỊ THEO MÔ HÌNH — KHÔNG PHẢI CẢM BIẾN',(18,height-20),
                cv2.FONT_HERSHEY_SIMPLEX,.45,(149,166,182),1,cv2.LINE_AA)
    return img


def decorate_video(frame,status,fps):
    cv2.rectangle(frame,(0,0),(frame.shape[1],45),(20,29,46),-1)
    color={'TRACKING':(96,209,144),'PREDICTED':(60,179,242),'LOST':(89,90,233)}.get(status,(177,177,177))
    put_text(frame,f'{status_text(status)}  |  {fps:.1f} khung/giây xử lý',(15,29),
                cv2.FONT_HERSHEY_SIMPLEX,.61,color,2,cv2.LINE_AA)
    return frame
