"""Chạy QWidget thật, kiểm tra tương tác và chụp Dashboard V4 ở ba kích thước.

Video sinh trong công cụ này là fixture tổng hợp có nhãn rõ ràng; không phải
dữ liệu đo cơ cấu thực và không được dùng để công bố độ chính xác thực tế.
"""

import argparse
import os
from pathlib import Path
import sys


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Kiểm chứng giao diện Dashboard V4 và chụp ảnh bằng Qt."
    )
    parser.add_argument(
        "--out",
        default="outputs/dashboard-v4-qa",
        help="Thư mục lưu ảnh và biên bản JSON",
    )
    parser.add_argument(
        "--native",
        action="store_true",
        help="Dùng cửa sổ hệ điều hành thay cho offscreen",
    )
    parser.add_argument(
        "--camera",
        action="store_true",
        help="Thử mở camera số 0; không lưu ảnh camera thực",
    )
    parser.add_argument(
        "--scale-factor",
        type=float,
        default=None,
        help="Hệ số thu phóng riêng cho tiến trình kiểm thử Qt",
    )
    args = parser.parse_args()
    if args.scale_factor is not None:
        os.environ["QT_SCALE_FACTOR"] = str(args.scale_factor)
    if not args.native:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtCore import (
        Qt,
        QTimer,
        QEventLoop,
        QRect,
        QCoreApplication,
        QEvent,
        QPoint,
        QPointF,
    )
    from PySide6.QtWidgets import QApplication, QLabel
    from PySide6.QtGui import QFontInfo
    from PySide6.QtTest import QTest
    import cv2
    import numpy as np
    import json
    import PySide6
    import pyqtgraph
    from mechavision.gui import MainWindow
    from mechavision.geometry import Geometry
    from mechavision.i18n import put_text

    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.settings.output_dir.setText("outputs/qa_dashboard_v4/sessions")
    window.experiments.output_root.setText("outputs/qa_dashboard_v4/experiments")
    window.show()
    notices = []
    window._notify = lambda title, text: notices.append(dict(title=title, text=text))
    record = dict(
        dashboard="V4",
        baseline="902d804833996aacf3b5ea5054314cd0150cbece",
        python=sys.version.split()[0],
        qt=PySide6.__version__,
        pyqtgraph=pyqtgraph.__version__,
        platform=app.platformName(),
        font_family=QFontInfo(window.shell.page_title.font()).family(),
        screenshots=[],
        bounds_issues=[],
        checks=[],
        camera=None,
    )

    def wait_until(condition, timeout=10000):
        if condition():
            return
        loop = QEventLoop()
        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: loop.quit() if condition() else None)
        deadline = QTimer()
        deadline.setSingleShot(True)
        deadline.timeout.connect(loop.quit)
        timer.start()
        deadline.start(timeout)
        loop.exec()
        timer.stop()
        deadline.stop()
        assert condition(), "Quá thời gian chờ giao diện"

    def capture(name, size, process_events=True):
        window.resize(*size)
        if process_events:
            app.processEvents()
        # Hoàn tất bố trí sau setText từ mẫu mới, không nhận thêm mẫu giữa hai bước.
        for _ in range(3):
            QCoreApplication.sendPostedEvents(None, QEvent.LayoutRequest)
        filename = f"{name}-{window.width()}x{window.height()}.png"
        screenshot = window.grab()
        assert screenshot.save(str(output / filename))
        metrics = window.state.metrics
        record["screenshots"].append(
            dict(
                file=filename,
                width=window.width(),
                height=window.height(),
                requested_width=size[0],
                requested_height=size[1],
                pixel_width=screenshot.width(),
                pixel_height=screenshot.height(),
                device_pixel_ratio=screenshot.devicePixelRatio(),
                phase=window.state.phase,
                source=window.state.mode,
                frames=window.state.sample_count,
                tracking=None if metrics is None else metrics["physics"].status,
                page=window.shell.stack.currentIndex(),
                camera_viewport=[
                    window.monitor.camera.width(),
                    window.monitor.camera.height(),
                ],
                twin_viewport=[
                    window.monitor.twin.width(),
                    window.monitor.twin.height(),
                ],
            )
        )
        for label in window.findChildren(QLabel):
            if not label.isVisible() or not label.text():
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
                record["bounds_issues"].append(
                    dict(
                        image=filename,
                        text=label.text(),
                        label_size=[label.width(), label.height()],
                        text_size=[bounds.width(), bounds.height()],
                    )
                )

    sizes = [(1366, 768), (1600, 900), (1920, 1080)]
    for size in sizes:
        window.navigate(0)
        capture("empty", size)
    window.resize(*sizes[0])
    QTest.mouseClick(window.start_btn, Qt.LeftButton)
    wait_until(lambda: window.state.sample_count >= 60)
    assert not notices, notices
    for size in sizes:
        for page, name in [(0, "monitoring"), (1, "analytics")]:
            QTest.mouseClick(window.shell.nav_buttons[page], Qt.LeftButton)
            capture(name, size)
    window.navigate(1)
    for tab, name in [(1,"analytics-quality"),(2,"analytics-performance")]:
        window.analysis.tabs.setCurrentIndex(tab)
        for size in sizes:
            capture(name,size)
    window.analysis.tabs.setCurrentIndex(0)
    window.navigate(0)
    QTest.mouseClick(window.monitor.focus_button, Qt.LeftButton)
    assert window.monitor.camera.focus_rect is None
    capture("monitoring-full-frame", sizes[0])
    QTest.mouseClick(window.monitor.focus_button, Qt.LeftButton)
    assert window.monitor.camera.focus_rect is not None
    record["checks"].append("closeup_and_full_frame_toggle")
    for _ in range(2):
        QTest.mouseClick(window.monitor.zoom_plus, Qt.LeftButton)
    assert window.monitor.camera.zoom_factor == 1.5
    capture("monitoring-zoom", sizes[0])
    for _ in range(2):
        QTest.mouseClick(window.monitor.zoom_minus, Qt.LeftButton)
    record["checks"].append("view_only_zoom")
    window.navigate(2)
    window.experiments.seconds.setValue(4)
    QTest.mouseClick(window.experiments.run_button, Qt.LeftButton)
    wait_until(
        lambda: (
            window.experiments.last_result is not None and not window.experiments.busy
        )
    )
    for size in sizes:
        capture("experiments", size)
    window.experiments.result_tabs.setCurrentIndex(1)
    for size in sizes:
        capture("experiments-table",size)
    window.experiments.result_tabs.setCurrentIndex(0)
    exported = output / "evaluation-synthetic-only.csv"
    original = window.experiments.export_results_to(exported)
    assert exported.read_bytes() == original.read_bytes()
    record["checks"].append("export_matches_original_evaluation_csv")
    QTest.mouseClick(window.stop_btn, Qt.LeftButton)
    wait_until(lambda: window.state.phase == "stopped")
    assert window.worker.wait(3000)
    # Kiểm tra lớp hiển thị trên mẫu đã dừng: không đổi quan sát/ước lượng.
    window.navigate(0)
    window.resize(*sizes[0])
    app.processEvents()
    stopped_metrics = window.state.metrics
    stopped_count = window.state.sample_count
    raw_image = window.monitor.camera.image.copy()
    QTest.mouseClick(window.monitor.annotation_button, Qt.LeftButton)
    assert not window.monitor.annotation_button.isChecked()
    assert window.monitor.camera.image == raw_image
    capture("monitoring-annotations-off", sizes[0])
    QTest.mouseClick(window.monitor.annotation_button, Qt.LeftButton)
    assert window.monitor.annotation_button.isChecked()
    window.monitor.camera.set_zoom(1.5)
    before_pan = QPointF(window.monitor.camera.pan_offset)
    center = window.monitor.camera.rect().center()
    QTest.mousePress(window.monitor.camera, Qt.LeftButton, pos=center)
    QTest.mouseMove(window.monitor.camera, center + QPoint(32, 18), delay=30)
    QTest.mouseRelease(
        window.monitor.camera, Qt.LeftButton, pos=center + QPoint(32, 18)
    )
    assert window.monitor.camera.pan_offset != before_pan
    QTest.mouseClick(window.monitor.fit_button, Qt.LeftButton)
    assert window.monitor.camera.zoom_factor == 1
    assert window.monitor.camera.pan_offset == QPointF()
    QTest.mouseClick(window.monitor.twin_zoom_plus, Qt.LeftButton)
    assert window.monitor.twin.zoom_factor > 1
    capture("monitoring-twin-zoom", sizes[0])
    QTest.mouseClick(window.monitor.twin_fit_button, Qt.LeftButton)
    assert window.monitor.twin.zoom_factor == 1
    assert window.monitor.twin.pan_offset == QPointF()
    assert window.state.metrics is stopped_metrics
    assert window.state.sample_count == stopped_count
    record["checks"].extend(
        [
            "annotation_toggle_preserves_raw_image",
            "camera_pan_fit",
            "twin_zoom_fit",
            "view_controls_preserve_state",
        ]
    )
    record["checks"].extend(
        [
            "start_simulation",
            "navigate_while_running",
            "background_evaluation",
            "stop_simulation",
        ]
    )
    window.source_mode.setCurrentIndex(window.source_mode.findData("camera"))
    for size in sizes:
        window.navigate(3)
        capture("settings", size)
    for tab,name in [(1,"settings-geometry"),(2,"settings-display")]:
        window.settings.tabs.setCurrentIndex(tab)
        for size in sizes:
            capture(name,size)
    window.settings.tabs.setCurrentIndex(0)

    # Dùng tệp video tổng hợp thật để đi qua decoder, detector, EKF và UI.
    fixture = root / "outputs/qa_dashboard_v4/fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    video = fixture / "synthetic_test_only.avi"
    geometry = fixture / "geometry.json"
    geo = Geometry()
    geo.to_json(geometry)
    writer = cv2.VideoWriter(
        str(video), cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (640, 400)
    )
    assert writer.isOpened()
    for frame_index in range(120):
        image = np.full((400, 640, 3), (31, 19, 7), dtype=np.uint8)
        if frame_index < 20:
            points = geo.points(0.4 + frame_index * 0.025)
            for key, point in points.items():
                color = {
                    "pivot": (0, 0, 255),
                    "crank": (0, 255, 0),
                    "piston": (255, 0, 0),
                }[key]
                cv2.circle(image, tuple(np.rint(point).astype(int)), 11, color, -1)
        put_text(
            image,
            "VIDEO TỔNG HỢP KIỂM THỬ — KHÔNG PHẢI CƠ CẤU THỰC",
            (15, 380),
            fontScale=0.55,
            color=(161, 137, 112),
        )
        writer.write(image)
    writer.release()
    window.source_mode.setCurrentIndex(window.source_mode.findData("video"))
    window.input_source.setText(str(video.relative_to(root)))
    window.geom_path.setText(str(geometry.relative_to(root)))
    window.navigate(0)
    window.resize(*sizes[0])
    window.start()
    wait_until(
        lambda: (
            window.state.metrics is not None
            and window.state.metrics["physics"].status == "PREDICTED"
        )
    )
    capture("video-predicted", sizes[0], process_events=False)
    wait_until(lambda: window.state.metrics["physics"].status == "LOST")
    for size in sizes:
        capture("video-lost", size)
        assert window.angle_label.text() == window.rpm_label.text() == "—"
    wait_until(lambda: window.state.phase == "stopped")
    assert window.worker.wait(3000)
    assert window.state.sample_count == 120
    record["checks"].extend(
        [
            "video_decoder_and_marker_detection",
            "predicted_state",
            "lost_state",
            "no_values_after_loss",
        ]
    )

    if args.camera:
        window.source_mode.setCurrentIndex(window.source_mode.findData("camera"))
        window.input_source.setText("0")
        window.geom_path.setText("configs/geometry.example.json")
        window.resize(*sizes[0])
        previous_notices = len(notices)
        window.start()
        capture("camera-connecting", sizes[0], process_events=False)
        wait_until(
            lambda: window.state.sample_count > 0 or window.state.phase == "error"
        )
        record["camera"] = dict(
            opened=window.state.sample_count > 0,
            error=window.state.error,
            note="Không xác minh cơ cấu/hiệu chuẩn và không lưu ảnh camera thực.",
        )
        if window.state.phase == "error":
            wait_until(lambda: window.start_btn.isEnabled())
            for size in sizes:
                capture("camera-error", size)
            assert len(notices) > previous_notices
        else:
            window.stop()
            wait_until(lambda: not window.worker.isRunning())
        record["checks"].append("camera_connection_or_reported_error")

    record["notices"] = notices
    (output / "qa-result.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    window.close()
    assert not record["bounds_issues"], record["bounds_issues"]
    print(
        json.dumps(
            dict(
                screenshots=len(record["screenshots"]),
                checks=record["checks"],
                bounds_issues=record["bounds_issues"],
                camera=record["camera"],
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
