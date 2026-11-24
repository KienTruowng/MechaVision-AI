"""Hiệu chuẩn hình học khớp bằng bốn lần nhấp trên một khung hình tĩnh."""
from __future__ import annotations
from .i18n import put_text
import cv2
import json
import math
import hashlib
from pathlib import Path
from .acquisition import FrameSource
from .geometry import Geometry

LABELS=('Tâm quay cố định O','Chốt khuỷu C','Khớp pít-tông–thanh truyền S','Chiều dương trục trượt')

def calibrate_interactively(source:int|str,output:str)->Geometry:
    with FrameSource(source) as capture:
        sample = capture.read()
        if sample is None:
            raise RuntimeError('Nguồn không cung cấp khung hình')
        image = sample[0]
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
            if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                raise RuntimeError('Đã đóng cửa sổ hiệu chuẩn')
            key=cv2.waitKey(30)&0xff
            if key in (27,ord('q')):raise RuntimeError('Đã hủy hiệu chuẩn')
            if key==ord('r'):pts.clear()
            if key in (10,13) and len(pts)==4:
                try:
                    geo=Geometry.from_landmarks(*pts)
                    save_calibration(geo, output, (image.shape[1], image.shape[0]))
                    return geo
                except ValueError as error:
                    print(f'Hiệu chuẩn chưa hợp lệ: {error}. Nhấn R để chọn lại.')
    finally:cv2.destroyWindow(win)


def save_calibration(geometry, output, image_size, mm_per_pixel=None):
    """Lưu hình học pixel và provenance; tỷ lệ mm chỉ do người đo cung cấp."""
    width, height = image_size
    if not all(isinstance(v, int) and v > 0 for v in (width, height)):
        raise ValueError('Kích thước ảnh phải là số nguyên dương')
    if mm_per_pixel is not None and (not math.isfinite(mm_per_pixel) or mm_per_pixel <= 0):
        raise ValueError('mm_per_pixel phải hữu hạn và dương')
    path = Path(output)
    geometry.to_json(path)
    meta = dict(image_size=[width, height], position_unit='pixel', angle_unit='degree',
                mm_per_pixel=mm_per_pixel, physically_validated=False,
                geometry_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    path.with_suffix('.calibration.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')


def validate_frame_size(geometry_path, width, height):
    path = Path(geometry_path)
    sidecar = path.with_suffix('.calibration.json')
    if not sidecar.exists():
        return  # Cấu hình cũ vẫn hỗ trợ; độ phân giải chưa được xác minh.
    meta = json.loads(sidecar.read_text(encoding='utf-8'))
    if meta['geometry_sha256'] != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError('Hình học đã đổi sau hiệu chuẩn; hãy lưu lại hiệu chuẩn')
    if meta['image_size'] != [width, height]:
        raise ValueError('Độ phân giải nguồn khác ảnh hiệu chuẩn; cần hiệu chuẩn lại, không tự scale phép đo')
