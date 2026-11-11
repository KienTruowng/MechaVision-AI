"""Chạy cửa sổ Windows, kiểm điều khiển và chụp bố cục Giám sát; dữ liệu mô phỏng."""

import os, sys, json

os.environ["QT_SCALE_FACTOR"] = "0.8"
from pathlib import Path
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QEventLoop, QTimer, Qt, QRect
from PySide6.QtTest import QTest
from mechavision.gui import MainWindow
import argparse

parser = argparse.ArgumentParser(description="Kiểm tra riêng trang Giám sát V4")
parser.add_argument("--out", default="outputs/monitoring-redesign")
args = parser.parse_args()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
app = QApplication([])
w = MainWindow()
w.resize(1600, 900)
w.show()


def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


wait(300)
w.grab().save(str(out / "empty-1600x900.png"))
w.start()
while w.state.sample_count < 60:
    wait(30)
shots = []
for width, height in [(1600, 900), (1366, 768)]:
    w.resize(width, height)
    wait(150)
    issues = []
    for label in w.findChildren(QLabel):
        if not label.isVisible() or label is w.session_text:
            continue
        flags = (
            Qt.TextWordWrap
            if label.wordWrap() or "\n" in label.text()
            else Qt.TextSingleLine
        )
        rect = label.fontMetrics().boundingRect(
            QRect(0, 0, label.width(), 10000), flags, label.text()
        )
        if rect.height() > label.height() + 3 or (
            not label.wordWrap() and rect.width() > label.width() + 3
        ):
            issues.append(label.text())
    name = f"monitoring-{width}x{height}.png"
    w.grab().save(str(out / name))
    shots.append(
        dict(
            file=name,
            size=w.size().toTuple(),
            camera=w.monitor.camera.size().toTuple(),
            twin=w.monitor.twin.size().toTuple(),
            bounds_issues=issues,
        )
    )
w.stop()
while w.worker and w.worker.isRunning():
    wait(30)
wait(50)
image = w.monitor.camera.image.copy()
QTest.mouseClick(w.monitor.annotation_button, Qt.LeftButton)
assert w.monitor.camera.image == image
QTest.mouseClick(w.monitor.zoom_plus, Qt.LeftButton)
assert w.monitor.camera.zoom_factor > 1
QTest.mouseClick(w.monitor.fit_button, Qt.LeftButton)
assert w.monitor.camera.zoom_factor == 1
(out / "qa.json").write_text(
    json.dumps(
        dict(
            executable=sys.executable,
            platform=app.platformName(),
            screenshots=shots,
            checks=["start", "stop", "annotations_preserve_frame", "zoom", "fit"],
        ),
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
w.close()
print(json.dumps(shots, ensure_ascii=True))
