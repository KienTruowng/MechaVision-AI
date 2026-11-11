"""Tương tác trên QWidget thật; dữ liệu video/che khuất dưới đây chỉ là fixture kiểm thử."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import csv
import json
import math
from pathlib import Path
import numpy as np
import cv2
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
from PySide6.QtCore import Qt, QTimer, QEventLoop, QRect, QThread
from PySide6.QtWidgets import QApplication, QLabel, QFileDialog
from PySide6.QtTest import QTest
from mechavision.gui import MainWindow
from mechavision.geometry import Geometry
from mechavision.processing import Processor
from mechavision.synthetic import Simulator, draw_mechanism
from mechavision.render import twin_frame
from mechavision.types import Observation, Estimate


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    widget = MainWindow()
    widget.resize(1366, 768)
    widget.show()
    errors = []
    widget._notify = lambda title, text: errors.append((title, text))
    widget.test_errors = errors
    yield widget
    if widget.worker and widget.worker.isRunning():
        widget.stop()
        assert widget.worker.wait(3000)
    if widget.experiments.busy:
        assert widget.experiments.worker.wait(5000)
    app.processEvents()
    widget.close()
    widget.deleteLater()
    app.processEvents()


def wait_until(condition, timeout=5000):
    if condition():
        return
    loop = QEventLoop()
    tick = QTimer()
    tick.setInterval(10)
    tick.timeout.connect(lambda: loop.quit() if condition() else None)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    tick.start()
    deadline.start(timeout)
    loop.exec()
    tick.stop()
    deadline.stop()
    assert condition(), "Quá thời gian chờ kết quả Qt"


def feed(window, count=15):
    geo = Geometry()
    simulator, processor = Simulator(geo), Processor(geo)
    obs = None
    for _ in range(count):
        obs = simulator.step()
        metrics = processor.step(obs)
        window._on_sample(
            draw_mechanism(geo, obs.truth_theta),
            twin_frame(geo, metrics["physics"]),
            dict(observation=obs, metrics=metrics, synthetic=True),
        )
    return geo, processor, obs


@pytest.mark.parametrize("size", [(1366, 700), (1366, 768), (1920, 1080)])
def test_four_pages_fit_and_have_no_clipped_labels(window, app, size):
    window.resize(*size)
    for index in range(4):
        QTest.mouseClick(window.shell.nav_buttons[index], Qt.LeftButton)
        app.processEvents()
        assert window.shell.stack.currentIndex() == index
        assert window.size().toTuple() == size
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
            assert bounds.height() <= label.height() + 3, label.text()
            if not label.wordWrap():
                assert bounds.width() <= label.width() + 3, label.text()


def test_initial_screen_has_no_fabricated_values(window):
    assert all(label.text() == "—" for label in window.monitor.kpis.labels.values())
    assert not window.camera_label.has_frame and not window.twin_label.has_frame
    assert window.state.sample_count == 0
    assert window.experiments.results_table.rowCount() == 0
    assert window.analysis.curves["physics_angle"].getData()[0] is None
    assert all(not card.sparkline.values for card in window.monitor.kpis.cards.values())
    assert all("—" in label.text() for label, _ in window.monitor.keypoint_labels.values())


def test_v3_trends_fps_and_sidebar_use_received_samples(window):
    _, processor, obs = feed(window, 95)
    window.navigate(1)
    for name, series in [("angle", "physics_angle"), ("rpm", "physics_rpm"),
                         ("sigma", "physics_sigma"), ("discrepancy", "discrepancy"), ("fps", "fps")]:
        values = list(window.state.series[series])
        np.testing.assert_allclose(window.monitor.kpis.cards[name].sparkline.values, values[-90:], equal_nan=True)
    np.testing.assert_allclose(window.analysis.curves["fps"].getData()[1], list(window.state.series["fps"]))
    assert "95 khung" in window.shell.sidebar_frames.text()
    assert window.shell.sidebar_source.text() == "MÔ PHỎNG"
    for name, (label, title) in window.monitor.keypoint_labels.items():
        assert label.text() == title + f" · {obs.landmarks[name].confidence:.2f}"
    processor.close()


def test_v3_zoom_changes_only_view_and_is_bounded(window):
    _, processor, _ = feed(window)
    image = window.camera_label.image.copy()
    metrics = window.state.metrics
    for _ in range(8):
        QTest.mouseClick(window.monitor.zoom_plus, Qt.LeftButton)
    assert window.camera_label.zoom_factor == 2
    assert window.monitor.zoom_text.text() == "2.00×"
    assert window.camera_label.image == image
    assert window.state.metrics is metrics
    for _ in range(8):
        QTest.mouseClick(window.monitor.zoom_minus, Qt.LeftButton)
    assert window.camera_label.zoom_factor == 1
    processor.close()


def test_start_navigate_stop_and_restart_without_stale_values(window):
    QTest.mouseClick(window.start_btn, Qt.LeftButton)
    wait_until(lambda: window.state.sample_count >= 5)
    first_log = window.state.log_path
    assert window.settings.locked and not window.source_mode.isEnabled()
    for index in [1, 2, 3, 0]:
        QTest.mouseClick(window.shell.nav_buttons[index], Qt.LeftButton)
        assert window.shell.stack.currentIndex() == index
    QTest.mouseClick(window.stop_btn, Qt.LeftButton)
    wait_until(lambda: window.state.phase == "stopped")
    assert window.worker.wait(3000)
    assert not window.settings.locked
    assert Path(first_log).is_file()
    QTest.mouseClick(window.start_btn, Qt.LeftButton)
    assert window.state.phase == "connecting"
    assert window.angle_label.text() == "—"
    assert not window.camera_label.has_frame
    wait_until(lambda: window.state.sample_count >= 3)
    assert first_log != window.state.log_path
    assert not window.test_errors


def test_sources_keep_their_values_and_yolo_controls(window):
    settings = window.settings
    settings.source_mode.setCurrentIndex(settings.source_mode.findData("camera"))
    settings.input_source.setText("3")
    settings.source_mode.setCurrentIndex(settings.source_mode.findData("video"))
    settings.input_source.setText("sample.mp4")
    settings.source_mode.setCurrentIndex(settings.source_mode.findData("camera"))
    assert settings.input_source.text() == "3"
    settings.source_mode.setCurrentIndex(settings.source_mode.findData("video"))
    assert settings.input_source.text() == "sample.mp4"
    settings.detector_mode.setCurrentIndex(settings.detector_mode.findData("yolo"))
    assert settings.weights_path.isEnabled() and settings.device.isEnabled()
    settings.source_mode.setCurrentIndex(settings.source_mode.findData("simulation"))
    assert not settings.weights_path.isEnabled()
    assert not settings.input_source.isEnabled()


def test_real_kpi_and_curves_do_not_mutate_estimator_results(window):
    _, _, _ = feed(window)
    window.navigate(1)
    metrics = window.state.metrics
    assert window.angle_label.text() == f"{math.degrees(metrics['physics'].theta):.1f}"
    for name in (
        "raw_angle",
        "temporal_angle",
        "physics_angle",
        "physics_rpm",
        "physics_sigma",
    ):
        _, values = window.analysis.curves[name].getData()
        np.testing.assert_allclose(
            values, list(window.state.series[name]), equal_nan=True
        )
    window.analysis.temporal_check.setChecked(False)
    assert not window.analysis.curves["temporal_angle"].isVisible()
    assert window.analysis.curves["physics_angle"].isVisible()
    window.analysis.follow_check.setChecked(False)
    window.angle_plot.setXRange(4, 8, padding=0)
    window.analysis.update_state(window.state)
    assert window.angle_plot.viewRange()[0] == pytest.approx([4, 8])


def test_actual_filter_loss_blanks_kpis_and_does_not_animate_twin(window):
    geo, processor, previous = feed(window)
    last_image = None
    for step in range(1, 40):
        obs = Observation(
            previous.timestamp + step / 30, {}, frame_id=previous.frame_id + step
        )
        metrics = processor.step(obs)
        image = twin_frame(geo, metrics["physics"])
        window._on_sample(
            np.zeros((390, 620, 3), dtype=np.uint8),
            image,
            dict(observation=obs, metrics=metrics, synthetic=True),
        )
        if last_image is not None and metrics["physics"].status == "LOST":
            np.testing.assert_array_equal(image, last_image)
        last_image = image if metrics["physics"].status == "LOST" else None
    assert window.state.metrics["physics"].status == "LOST"
    assert window.angle_label.text() == window.rpm_label.text() == "—"
    assert window.state_label.text() == "Mất dấu"
    assert "Không đủ độ tin cậy" in window.confidence_label.text()
    assert math.isnan(window.state.series["physics_angle"][-1])


def test_camera_connecting_and_error_restore_controls(window, monkeypatch, tmp_path):
    from mechavision import dashboard_controller

    geometry = tmp_path / "geometry.json"
    Geometry().to_json(geometry)
    window.geom_path.setText(str(geometry))
    window.source_mode.setCurrentIndex(window.source_mode.findData("camera"))

    class FailedSource:
        def __init__(self, source):
            raise RuntimeError("Nguồn camera kiểm thử không khả dụng")

    monkeypatch.setattr(dashboard_controller, "FrameSource", FailedSource)
    window.start()
    assert window.monitor.tracking_badge.text() == "ĐANG KẾT NỐI"
    wait_until(lambda: window.state.phase == "error" and window.start_btn.isEnabled())
    assert window.worker.wait(3000)
    assert window.test_errors
    assert not window.settings.locked
    assert window.shell.system_badge.text() == "PHIÊN LỖI"
    assert window.angle_label.text() == "—"


def test_video_uses_actual_marker_detections_and_reaches_loss(window, tmp_path):
    geo = Geometry()
    geometry = tmp_path / "geometry.json"
    geo.to_json(geometry)
    video = tmp_path / "synthetic_test_only.avi"
    writer = cv2.VideoWriter(
        str(video), cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (640, 400)
    )
    assert writer.isOpened()
    for frame in range(60):
        image = np.zeros((400, 640, 3), dtype=np.uint8)
        if frame < 20:
            for key, position in geo.points(0.4 + frame * 0.025).items():
                color = {
                    "pivot": (0, 0, 255),
                    "crank": (0, 255, 0),
                    "piston": (255, 0, 0),
                }[key]
                cv2.circle(image, tuple(np.rint(position).astype(int)), 10, color, -1)
        writer.write(image)
    writer.release()
    window.source_mode.setCurrentIndex(window.source_mode.findData("video"))
    window.input_source.setText(str(video))
    window.geom_path.setText(str(geometry))
    window.start()
    wait_until(lambda: window.state.phase == "stopped")
    assert window.worker.wait(3000)
    assert window.state.sample_count == 60
    assert window.state.metrics["physics"].status == "LOST"
    assert window.angle_label.text() == "—"
    assert window.camera_label.has_frame and not window.test_errors
    with open(window.state.log_path, encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 60
    assert any(row["status"] == "TRACKING" for row in rows)
    assert rows[-1]["status"] == "LOST" and rows[-1]["theta_rad"] == ""


def test_geometry_file_picker_interaction(window, app, tmp_path):
    target = tmp_path / "hinh_hoc.json"
    Geometry().to_json(target)

    def choose():
        dialog = app.activeModalWidget()
        assert isinstance(dialog, QFileDialog)
        dialog.selectFile(str(target))
        dialog.accept()

    QTimer.singleShot(30, choose)
    window._browse(window.geom_path, "JSON (*.json)")
    assert Path(window.geom_path.text()) == target


def test_evaluation_runs_off_ui_thread_and_matches_original(window, monkeypatch):
    from mechavision import evaluation

    original = evaluation.run_evaluation
    threads = []

    def observed(*args, **kwargs):
        threads.append(QThread.currentThread())
        return original(*args, **kwargs)

    monkeypatch.setattr(evaluation, "run_evaluation", observed)
    page = window.experiments
    page.seconds.setValue(4)
    page.run_evaluation()
    assert not page.run_button.isEnabled()
    wait_until(lambda: page.last_result is not None and not page.busy)
    assert threads[0] != QApplication.instance().thread()
    reference = original(seconds=4, fps=30, seed=42, noise_px=3)
    assert page.last_result == reference
    assert page.results_table.rowCount() == 3
    stored = json.loads(
        (Path(page.last_output) / "summary.json").read_text(encoding="utf-8")
    )
    assert stored == reference


def test_image_surface_owns_its_frame_and_survives_resize(window, app):
    frame = np.full((80, 160, 3), (7, 15, 29), dtype=np.uint8)
    window.camera_label.set_frame(frame)
    frame[:] = 0
    assert window.camera_label.image.pixelColor(0, 0).getRgb()[:3] == (29, 15, 7)
    for size in [(1366, 768), (1920, 1080)]:
        window.resize(*size)
        app.processEvents()
        assert window.camera_label.has_frame
        assert not window.camera_label.grab().isNull()


def test_closeup_toggle_keeps_original_image_and_measurements(window, app):
    geo, processor, _ = feed(window)
    image = window.camera_label.image.copy()
    metrics = window.state.metrics
    region = window.camera_label.focus_rect
    assert region is not None and region.width() < image.width()
    for angle in np.linspace(0, 2 * math.pi, 180):
        for x, y in geo.points(angle).values():
            assert region.left() <= x <= region.right()
            assert region.top() <= y <= region.bottom()
    QTest.mouseClick(window.monitor.focus_button, Qt.LeftButton)
    app.processEvents()
    assert window.camera_label.focus_rect is None
    assert window.monitor.focus_button.accessibleName() == "Toàn khung"
    QTest.mouseClick(window.monitor.focus_button, Qt.LeftButton)
    assert window.camera_label.focus_rect == region
    assert window.camera_label.image == image
    assert window.state.metrics is metrics
    processor.close()


def test_twin_resize_renders_same_estimate_without_advancing_time(window, app):
    from mechavision.dashboard_widgets import ImageSurface

    geo, processor, _ = feed(window)
    estimate = window.state.metrics["physics"]
    reference = ImageSurface("", "")
    for size in [(1366, 768), (1920, 1080)]:
        window.resize(*size)
        app.processEvents()
        surface = window.monitor.twin
        assert surface.image.size() == surface.size()
        reference.set_frame(twin_frame(geo, estimate, surface.width(), surface.height()))
        assert surface.image == reference.image
        previous = surface.image.copy()
        QTest.qWait(35)
        assert surface.image == previous
        assert surface.estimate is estimate
    processor.close()


@pytest.mark.parametrize("axis,offset", [(0, 0), (35, 80), (-90, -80)])
def test_closeup_uses_selected_calibration_and_stays_fixed(window, axis, offset):
    geometry = Geometry(axis_deg=axis, slider_offset_px=offset)
    window.monitor.set_geometry(geometry)
    region = window.camera_label.focus_rect
    for theta in np.linspace(0, 2 * math.pi, 180):
        for x, y in geometry.points(theta).values():
            assert region.left() <= x <= region.right()
            assert region.top() <= y <= region.bottom()
    assert window.camera_label.focus_rect == region


@pytest.mark.parametrize("status", ["LOST", "UNINITIALIZED"])
def test_twin_rejects_angles_from_invalid_status(status):
    geo = Geometry()
    first = twin_frame(geo, Estimate(1.0, theta=0.5, status=status))
    second = twin_frame(geo, Estimate(2.0, theta=2.0, status=status))
    np.testing.assert_array_equal(first, second)


def test_recorded_evaluation_uses_original_csv_reference_pipeline(window, tmp_path):
    from mechavision.session import SessionWriter
    from mechavision.real_ablation import real_ablation

    geo = Geometry()
    simulator, processor = Simulator(geo), Processor(geo)
    geometry = tmp_path / "geometry.json"
    geo.to_json(geometry)
    session, truth = tmp_path / "fixture.csv", tmp_path / "reference.csv"
    with (
        SessionWriter(session) as writer,
        truth.open("w", encoding="utf-8", newline="") as stream,
    ):
        reference = csv.writer(stream)
        reference.writerow(["frame", "theta_rad"])
        for _ in range(45):
            obs = simulator.step()
            metrics = processor.step(obs)
            writer.write(obs, metrics["physics"])
            reference.writerow([obs.frame_id, obs.truth_theta])
    page = window.experiments
    page.mode.setCurrentIndex(page.mode.findData("recorded"))
    page.session_file.setText(str(session))
    page.truth_file.setText(str(truth))
    page.geometry_file.setText(str(geometry))
    page.run_evaluation()
    wait_until(lambda: page.last_result is not None and not page.busy)
    expected = real_ablation(
        str(session), str(truth), str(geometry), str(tmp_path / "expected")
    )
    assert page.last_result == expected
    assert page.result_badge.text() == "QUAN SÁT ĐÃ GHI"
    assert page.results_table.rowCount() == 3
    exported = tmp_path / "export-recorded.csv"
    original = page.export_results_to(exported)
    assert original.name == "real_ablation.csv"
    assert exported.read_bytes() == (tmp_path / "expected" / "real_ablation.csv").read_bytes()
