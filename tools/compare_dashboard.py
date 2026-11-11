"""Ghép ảnh QA thật để đối chiếu bố cục; không dựng hoặc thay thế dữ liệu giao diện."""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from mechavision.i18n import _font


def compare(left_path, right_path, output, left_title, right_title):
    images = []
    for path in (left_path, right_path):
        with Image.open(path) as source:
            image = source.convert("RGB")
        image.thumbnail((960, 700), Image.Resampling.LANCZOS)
        images.append(image)
    gap, margin, heading = 20, 20, 52
    width = 2 * 960 + gap + 2 * margin
    height = max(image.height for image in images) + heading + margin
    canvas = Image.new("RGB", (width, height), "#060f18")
    draw = ImageDraw.Draw(canvas)
    for column, (image, title) in enumerate(zip(images, (left_title, right_title))):
        x = margin + column * (960 + gap)
        draw.text((x, 13), title, font=_font(22), fill="#dce7f4")
        canvas.paste(image, (x + (960 - image.width) // 2, heading))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Ghép ảnh V3/V4 và ảnh tham chiếu để review trực quan."
    )
    parser.add_argument(
        "--before", type=Path, default=Path("assets/dashboard-v3/exact")
    )
    parser.add_argument("--after", type=Path, default=Path("assets/dashboard-v4/exact"))
    parser.add_argument(
        "--out", type=Path, default=Path("assets/dashboard-v4/comparisons")
    )
    parser.add_argument(
        "--reference",
        type=Path,
        help="Ảnh tham chiếu người dùng cung cấp, chỉ dùng trong ảnh đối chiếu",
    )
    args = parser.parse_args()
    count = 0
    for page, title in (
        ("monitoring", "Giám sát"),
        ("analytics", "Phân tích"),
        ("experiments", "Thực nghiệm"),
        ("settings", "Cài đặt"),
    ):
        for size in ("1366x768", "1920x1080"):
            name = f"{page}-{size}.png"
            before, after = args.before / name, args.after / name
            if before.is_file() and after.is_file():
                compare(
                    before,
                    after,
                    args.out / name,
                    f"V3 · {title} · {size}",
                    f"V4 · {title} · {size}",
                )
                count += 1
    if args.reference:
        compare(
            args.reference,
            args.after / "monitoring-1366x768.png",
            args.out / "reference-v4.png",
            "Ảnh tham chiếu người dùng · Sentinex",
            "MechaVision AI V4 · Ảnh ứng dụng thực tế",
        )
        count += 1
    if count == 0:
        raise SystemExit("Chưa có cặp ảnh QA phù hợp để ghép.")
    print(f"Đã lưu {count} ảnh đối chiếu trong {args.out}")


if __name__ == "__main__":
    main()
