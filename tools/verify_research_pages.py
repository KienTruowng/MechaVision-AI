"""QA Windows ba trang nghiên cứu V4; chỉ dùng dữ liệu mô phỏng có nhãn."""

import os

os.environ["QT_SCALE_FACTOR"] = "0.8"
import argparse
import json
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QEventLoop, QTimer, Qt, QRect
from PySide6.QtTest import QTest
from mechavision.gui import MainWindow

parser = argparse.ArgumentParser()
parser.add_argument("--out", default="outputs/research-pages-qa")
parser.add_argument("--main-only", action="store_true")
args = parser.parse_args()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
app = QApplication([])
window = MainWindow()
window.resize(1600, 900)
window.show()
window.settings.output_dir.setText(str(out / "sessions"))
window.experiments.output_root.setText(str(out / "experiments"))


def wait(ms=120):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def until(condition):
    end = time.monotonic() + 15
    while not condition() and time.monotonic() < end:
        wait(30)
    assert condition(), "Quá thời gian chờ"


shots = []


def capture(name):
    if args.main_only and name not in ("analytics", "experiments", "settings"):
        return
    wait()
    issues = []
    for label in window.findChildren(QLabel):
        if not label.isVisible() or label is window.session_text:
            continue
        flags = (
            Qt.TextWordWrap
            if label.wordWrap() or "\n" in label.text()
            else Qt.TextSingleLine
        )
        bounds = label.fontMetrics().boundingRect(
            QRect(0, 0, label.width(), 10000), flags, label.text()
        )
        if bounds.height() > label.height() + 3 or (
            not label.wordWrap() and bounds.width() > label.width() + 3
        ):
            issues.append(label.text())
    window.grab().save(str(out / (name + "-1600x900.png")))
    shots.append(dict(page=name, size=window.size().toTuple(), bounds_issues=issues))


window.navigate(1)
capture("analytics-empty")
window.start()
until(lambda: window.state.sample_count >= 100)
window.stop()
until(lambda: window.worker is None or not window.worker.isRunning())
window.navigate(1)
for index, name in enumerate(
    ["analytics", "analytics-quality", "analytics-performance"]
):
    window.analysis.tabs.setCurrentIndex(index)
    capture(name)
window.navigate(2)
window.experiments.seconds.setValue(3)
window.experiments.run_evaluation()
until(
    lambda: window.experiments.last_result is not None and not window.experiments.busy
)
capture("experiments")
window.experiments.result_tabs.setCurrentIndex(1)
capture("experiments-table")
export = out / "evaluation-simulation-only.csv"
original = window.experiments.export_results_to(export)
assert export.read_bytes() == Path(original).read_bytes()
assert window.experiments.session_list.count() == 1
window.navigate(3)
for index, name in enumerate(["settings", "settings-geometry", "settings-display"]):
    QTest.mouseClick(window.settings.group_buttons[index], Qt.LeftButton)
    assert window.settings.tabs.currentIndex() == index
    capture(name)
window.close()
(out / "qa.json").write_text(
    json.dumps(
        dict(
            platform=app.platformName(),
            shots=shots,
            checks=[
                "simulation_start_stop",
                "settings_group_navigation",
                "evaluation_worker",
                "csv_matches_pipeline",
                "session_history",
            ],
        ),
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(shots, ensure_ascii=True))
assert not any(shot["bounds_issues"] for shot in shots)
