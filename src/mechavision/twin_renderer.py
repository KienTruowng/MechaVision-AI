"""Bản vẽ cơ khí V4; chỉ biến đổi hiển thị, không bổ sung mô hình động lực học.

Mặt trước dùng một tỷ lệ duy nhất cho cả hai trục. Các mặt cạnh và bóng đổ
chỉ biểu diễn bề dày của chi tiết; tâm O/C/S vẫn nằm đúng mặt phẳng động học.
"""

from functools import lru_cache
import math

import cv2
import numpy as np

from .i18n import put_text
from .geometry import Geometry


CYAN = (227, 217, 91)
VIOLET = (222, 151, 157)
TEXT = (224, 214, 197)
MUTED = (151, 133, 111)
EDGE = (107, 86, 62)
AA = cv2.LINE_AA


def _polygon(image, vertices, color, edge=None):
    points = np.rint(vertices).astype(np.int32)
    cv2.fillPoly(image, [points], color, AA)
    if edge is not None:
        cv2.polylines(image, [points], True, edge, 1, AA)


def _bolt(image, point, radius=4):
    radius = max(2, int(radius))
    if radius == 7:
        radius = 6
    cv2.circle(image, point, radius + 2, (30, 22, 14), -1, AA)
    cv2.circle(image, point, radius, (171, 150, 122), -1, AA)
    cv2.line(
        image,
        (point[0] - radius + 1, point[1]),
        (point[0] + radius - 1, point[1]),
        (55, 41, 28),
        1,
        AA,
    )


def _metal_box(image, rect, depth=8, accent=EDGE):
    """Mặt trước trung tính, mặt trên sáng và mặt cạnh tối; không dùng glow."""
    left, top, right, bottom = map(int, rect)
    _polygon(
        image,
        [
            (left + 4, top + depth),
            (right + depth, top + depth),
            (right + depth, bottom + depth),
            (left + 4, bottom + depth),
        ],
        (12, 9, 6),
    )
    _polygon(
        image,
        [
            (left, top),
            (left + depth, top - depth),
            (right + depth, top - depth),
            (right, top),
        ],
        (142, 120, 91),
        (182, 159, 126),
    )
    _polygon(
        image,
        [
            (right, top),
            (right + depth, top - depth),
            (right + depth, bottom - depth),
            (right, bottom),
        ],
        (61, 45, 29),
        EDGE,
    )
    cv2.rectangle(image, (left, top), (right, bottom), (84, 64, 44), -1)
    # Bề mặt thép có chuyển sắc theo bề dày; chỉ thay vật liệu minh họa.
    for y in range(max(0, top + 1), min(image.shape[0], bottom)):
        t = (y - top) / max(1, bottom - top)
        shade = tuple(
            int(a * (1 - t) + b * t) for a, b in zip((132, 117, 95), (64, 54, 42))
        )
        cv2.line(
            image,
            (max(0, left + 1), y),
            (min(image.shape[1] - 1, right - 1), y),
            shade,
            1,
        )
    cv2.rectangle(image, (left, top), (right, bottom), accent, 1, AA)
    cv2.line(image, (left + 1, top + 1), (right - 1, top + 1), (201, 175, 138), 1, AA)


@lru_cache(maxsize=12)
def _layout(radius, rod, offset, width, height):
    # Chỉ lấy mẫu để đặt miền nhìn cố định; gọi nguyên hàm động học hiện có.
    angles = np.linspace(0, 2 * math.pi, 361)
    geometry = Geometry(radius_px=radius, rod_px=rod, slider_offset_px=offset)
    positions = np.array([geometry.slider_x(angle) for angle in angles])
    left_slider, right_slider = float(positions.min()), float(positions.max())
    xmin, xmax = -radius * 1.14, right_slider + radius * 0.48
    ymin = min(-radius * 1.12, offset - radius * 0.62)
    ymax = max(radius * 1.12, offset + radius * 0.62)
    top = 82 if height >= 300 else 44
    bottom = height - 43
    scale = max(0.01, min((width - 42) / (xmax - xmin), (bottom - top) / (ymax - ymin)))
    center = np.array([width / 2, (top + bottom) / 2])
    midpoint = np.array([(xmin + xmax) / 2, (ymin + ymax) / 2])
    return scale, center, midpoint, left_slider, right_slider, top, bottom


def _point(position, scale, center, midpoint):
    return tuple(
        np.rint(center + (np.asarray(position) - midpoint) * (scale, -scale)).astype(
            int
        )
    )


@lru_cache(maxsize=12)
def _backdrop(width, height):
    image = np.full((height, width, 3), (26, 17, 9), dtype=np.uint8)
    top = 52 if height >= 300 else 32
    for x in range(24, width - 16, 40):
        for y in range(top, height - 35, 40):
            image[y : y + 2, x : x + 2] = (56, 41, 27)
    cv2.line(image, (18, height - 31), (width - 18, height - 31), (66, 47, 31), 1)
    image.setflags(write=False)
    return image


@lru_cache(maxsize=12)
def _assembly(radius, rod, offset, width, height):
    """Lưu chi tiết cố định để không dựng lại xi-lanh và bệ trong mỗi khung."""
    image = _backdrop(width, height).copy()
    scale, center, midpoint, left_slider, right_slider, top, bottom = _layout(
        radius, rod, offset, width, height
    )
    xy = lambda position: _point(position, scale, center, midpoint)
    origin = xy((0, 0))
    orbit = max(1, round(radius * scale))
    # Quỹ đạo là đường hình học toàn vòng, không phải lịch sử quan sát.
    for angle in range(0, 360, 12):
        cv2.ellipse(
            image, origin, (orbit, orbit), 0, angle, angle + 7, (102, 73, 46), 1, AA
        )
    cv2.arrowedLine(
        image,
        (23, origin[1]),
        (width - 22, origin[1]),
        (96, 68, 41),
        1,
        tipLength=0.015,
    )
    cv2.arrowedLine(
        image, (origin[0], bottom), (origin[0], top), (96, 68, 41), 1, tipLength=0.03
    )
    put_text(image, "x", (width - 23, origin[1] - 7), fontScale=0.42, color=MUTED)
    put_text(image, "y", (origin[0] + 6, top + 5), fontScale=0.42, color=MUTED)

    # Xi-lanh cắt bổ và ray trượt: khoảng hành trình được tính từ hình học đã chọn.
    left, axis_y = xy((left_slider - radius * 0.23, offset))
    right = xy((right_slider + radius * 0.30, offset))[0]
    half = max(18, round(radius * scale * 0.42))
    thickness = max(6, round(half * 0.20))
    depth = max(4, min(10, round(scale * 5)))
    cv2.rectangle(
        image, (left, axis_y - half), (right, axis_y + half), (35, 26, 17), -1
    )
    for rail_y in [axis_y - half - thickness, axis_y + half]:
        _metal_box(image, (left, rail_y, right, rail_y + thickness), depth)
        cv2.line(
            image,
            (left + 6, rail_y + thickness // 2),
            (right - 6, rail_y + thickness // 2),
            (197, 177, 145),
            1,
            AA,
        )
    _metal_box(
        image,
        (
            right,
            axis_y - half - thickness,
            right + thickness,
            axis_y + half + thickness,
        ),
        depth,
    )
    for x in [left + 8, right - 8]:
        for y in [axis_y - half - thickness // 2, axis_y + half + thickness // 2]:
            _bolt(image, (x, y), 3)

    # Bệ ổ trục và trục khuỷu đồng tâm O; đường kính mang ý nghĩa minh họa chi tiết.
    bearing = max(18, min(40, round(orbit * 0.32)))
    foot_y = origin[1] + bearing + 2
    _metal_box(
        image,
        (origin[0] - bearing - 7, foot_y, origin[0] + bearing + 7, foot_y + 8),
        depth,
    )
    cv2.circle(
        image, (origin[0] + depth, origin[1] - depth), bearing, (75, 55, 36), -1, AA
    )
    cv2.circle(image, origin, bearing, (141, 119, 89), -1, AA)
    cv2.circle(image, origin, bearing, (206, 180, 139), 1, AA)
    cv2.circle(image, origin, max(8, bearing - 5), (47, 32, 19), -1, AA)
    cv2.circle(image, origin, max(8, bearing - 9), (119, 99, 72), 2, AA)
    for angle in np.linspace(0, 2 * math.pi, 9)[:-1]:
        center_ball = (
            round(origin[0] + (bearing - 7) * math.cos(angle)),
            round(origin[1] + (bearing - 7) * math.sin(angle)),
        )
        cv2.circle(image, center_ball, 3, (200, 190, 165), -1, AA)
        cv2.circle(image, center_ball, 3, (75, 61, 44), 1, AA)
    for x in [origin[0] - bearing, origin[0] + bearing]:
        _bolt(image, (x, foot_y + 4), 2)
    image.setflags(write=False)
    return image


def _link(image, first, second, thickness, accent, depth):
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    direction = b - a
    normal = np.array([-direction[1], direction[0]]) / max(1, np.linalg.norm(direction))
    inner_a, inner_b = a + direction * 0.12, b - direction * 0.12
    outline = [
        a + normal * thickness * 0.65,
        inner_a + normal * thickness * 0.48,
        inner_b + normal * thickness * 0.48,
        b + normal * thickness * 0.65,
        b - normal * thickness * 0.65,
        inner_b - normal * thickness * 0.48,
        inner_a - normal * thickness * 0.48,
        a - normal * thickness * 0.65,
    ]
    shadow = np.asarray(outline) + (depth, depth)
    _polygon(image, shadow, (10, 8, 6))
    _polygon(image, np.asarray(outline) + (depth, -depth), (69, 52, 35), EDGE)
    _polygon(image, outline, (162, 145, 118), (220, 203, 170))
    # Rãnh giữa thanh truyền và biên kỹ thuật; không dịch tâm khớp.
    cv2.line(
        image,
        tuple(np.rint(inner_a).astype(int)),
        tuple(np.rint(inner_b).astype(int)),
        (66, 48, 31),
        max(3, int(thickness * 0.50)),
        AA,
    )
    highlight_a = tuple(np.rint(a - normal * thickness * 0.48).astype(int))
    highlight_b = tuple(np.rint(b - normal * thickness * 0.48).astype(int))
    cv2.line(image, highlight_a, highlight_b, accent, 2, AA)


def render_twin(geo, estimate, width=620, height=390):
    """Chỉ vẽ tư thế ước lượng hợp lệ; không có đồng hồ hay trạng thái chuyển động riêng."""
    width, height = int(width), int(height)
    valid = (
        estimate is not None
        and estimate.theta is not None
        and math.isfinite(estimate.theta)
        and estimate.status in ("TRACKING", "PREDICTED")
    )
    params = (geo.radius_px, geo.rod_px, geo.slider_offset_px, width, height)
    image = (_assembly(*params) if valid else _backdrop(width, height)).copy()
    predicted = estimate is not None and estimate.status == "PREDICTED"
    label = "DỰ BÁO THEO MÔ HÌNH" if predicted else "TRẠNG THÁI ƯỚC LƯỢNG"
    color = (109, 196, 243) if predicted else CYAN
    if not valid:
        label = "CHƯA CÓ ƯỚC LƯỢNG HỢP LỆ"
        color = MUTED
    put_text(image, label, (18, 23), fontScale=0.43, color=color)
    put_text(
        image,
        f"r {geo.radius_px:g} px   ·   l {geo.rod_px:g} px   ·   e {geo.slider_offset_px:g} px",
        (18, height - 11),
        fontScale=0.45,
        color=MUTED,
    )
    if not valid:
        put_text(
            image,
            "Không đủ độ tin cậy để dựng cơ cấu",
            (24, height // 2),
            fontScale=0.56,
            color=TEXT,
        )
        put_text(
            image,
            "Chờ quan sát được bộ lọc chấp nhận",
            (24, height // 2 + 25),
            fontScale=0.44,
            color=MUTED,
        )
        return image

    scale, center, midpoint, _, _, _, _ = _layout(*params)
    xy = lambda point: _point(point, scale, center, midpoint)
    theta = estimate.theta
    origin = xy((0, 0))
    crank = xy((geo.radius_px * math.cos(theta), geo.radius_px * math.sin(theta)))
    piston = xy((geo.slider_x(theta), geo.slider_offset_px))
    size = geo.radius_px * scale
    depth = max(4, min(9, round(size * 0.075)))
    crank_width = max(16, min(38, size * 0.32))
    rod_width = max(14, min(30, size * 0.25))
    _link(image, origin, crank, crank_width, VIOLET, depth)
    _link(image, crank, piston, rod_width, CYAN, depth)
    half_w = max(12, min(28, round(size * 0.22)))
    half_h = max(14, round(size * 0.34))
    _metal_box(
        image,
        (
            piston[0] - half_w,
            piston[1] - half_h,
            piston[0] + half_w,
            piston[1] + half_h,
        ),
        depth,
        CYAN,
    )
    for offset in [-half_w + 5, half_w - 5]:
        cv2.line(
            image,
            (piston[0] + offset, piston[1] - half_h + 3),
            (piston[0] + offset, piston[1] + half_h - 3),
            (214, 192, 155),
            2,
            AA,
        )
    for name, point in [("O", origin), ("C", crank), ("S", piston)]:
        cv2.circle(image, point, 12, (50, 35, 21), -1, AA)
        cv2.circle(image, point, 10, (199, 181, 149), -1, AA)
        cv2.circle(image, point, 7, (40, 29, 17), -1, AA)
        cv2.circle(image, point, 7, (232, 218, 191), 1, AA)
        cv2.circle(image, point, 3, (175, 150, 114), -1, AA)
        put_text(image, name, (point[0] - 4, point[1] - 19), fontScale=0.46, color=TEXT)
    put_text(
        image,
        f"θ {math.degrees(theta):.1f}°",
        (max(18, width - 126), 23),
        fontScale=0.52,
        color=TEXT,
    )
    return image
