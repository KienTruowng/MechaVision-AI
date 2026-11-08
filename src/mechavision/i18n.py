"""Nhãn tiếng Việt và bộ vẽ Unicode cho ảnh OpenCV; giữ nguyên mã dữ liệu."""
from functools import lru_cache
from pathlib import Path
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont


STATUS_LABELS = {
    'UNINITIALIZED': 'Chưa khởi tạo',
    'TRACKING': 'Đang theo dõi',
    'PREDICTED': 'Đang dự báo',
    'LOST': 'Mất dấu',
}
KEYPOINT_LABELS = {
    'pivot': 'Tâm quay',
    'crank': 'Chốt khuỷu',
    'piston': 'Khớp pít-tông',
}


def status_text(status):
    return STATUS_LABELS.get(status, 'Trạng thái không xác định')


@lru_cache(maxsize=64)
def _font(size):
    """Ưu tiên phông hệ thống có đầy đủ dấu tiếng Việt trên Windows/macOS/Linux."""
    candidates = [
        str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'segoeui.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        'DejaVuSans.ttf',
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    raise RuntimeError('Không tìm thấy phông Unicode. Hãy cài Segoe UI, DejaVu Sans hoặc Noto Sans.')


@lru_cache(maxsize=1024)
def _text_mask(text, size, stroke, available):
    font = _font(size)
    box = font.getbbox(text, stroke_width=stroke)
    while box[2] - box[0] > available and size > 6:
        size -= 1
        font = _font(size)
        box = font.getbbox(text, stroke_width=stroke)
    width = max(1, box[2] - box[0])
    height = max(1, box[3] - box[1])
    mask = Image.new('L', (width, height))
    ImageDraw.Draw(mask).text((-box[0], -box[1]), text, font=font,
                              fill=255, stroke_width=stroke, stroke_fill=255)
    return np.asarray(mask, dtype=np.float32)[:, :, None] / 255


def put_text(image, text, org, fontFace=None, fontScale=.5,
             color=(255, 255, 255), thickness=1, lineType=None):
    """Vẽ vào ảnh BGR tại đường cơ sở; thu chữ vừa chiều ngang, tránh cắt nhãn.

    Các đối số vị trí tương thích với những lệnh cv2.putText hiện có.
    Chỉ xử lý vùng chữ, không chuyển đổi toàn bộ khung hình qua Pillow.
    """
    height, width = image.shape[:2]
    x = max(0, min(int(org[0]), width - 1))
    mask = _text_mask(str(text), max(6, round(fontScale * 28)),
                      max(0, thickness - 1), width - x)
    h, w = mask.shape[:2]
    y = max(0, min(int(org[1]) - h, height - h))
    h = min(h, height - y)
    w = min(w, width - x)
    alpha = mask[:h, :w]
    region = image[y:y+h, x:x+w]
    region[:] = np.rint(region * (1 - alpha) + np.asarray(color) * alpha).astype(np.uint8)
    return image
