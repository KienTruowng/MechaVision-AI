"""Kiểm thử hồi quy V4 trên dữ liệu thực sự đã nhận và các điều khiển hiển thị."""

import math
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtTest import QTest
from test_dashboard_v2 import app, window, feed, wait_until
from mechavision.types import Observation, Estimate
from mechavision.geometry import Geometry
from mechavision.render import twin_frame


def test_raw_frame_annotation_pan_and_preferences_preserve_measurement(window, app):
    window.start()
    wait_until(lambda: window.state.sample_count >= 5)
    window.stop()
    wait_until(lambda: window.state.phase == "stopped")
    camera = window.monitor.camera
    image, metrics = camera.image.copy(), window.state.metrics
    assert camera.observation is window.state.observation
    annotated = camera.grab().toImage()
    window.settings.annotation_check.setChecked(False)
    assert not window.monitor.annotation_button.isChecked()
    assert not camera.show_annotations
    assert camera.grab().toImage() != annotated
    assert camera.image == image
    window.monitor.annotation_button.setChecked(True)
    assert window.settings.annotation_check.isChecked()
    camera.set_zoom(1.5)
    camera.grab()
    center = camera.rect().center()
    QTest.mousePress(camera, Qt.LeftButton, pos=center)
    QTest.mouseMove(camera, center + QPoint(30, 15), delay=20)
    QTest.mouseRelease(camera, Qt.LeftButton, pos=center + QPoint(30, 15))
    assert camera.pan_offset != QPointF()
    QTest.mouseClick(window.monitor.fit_button, Qt.LeftButton)
    assert camera.pan_offset == QPointF() and camera.zoom_factor == 1
    assert window.state.metrics is metrics and camera.image == image


def test_diagnostics_and_missing_confidence_keep_original_values(window):
    geo, processor, previous = feed(window)
    page = window.analysis
    obs, metrics = window.state.observation, window.state.metrics
    assert page.diagnostics["processing_ms"][-1] == metrics["processing_ms"]
    for name in ("pivot", "crank", "piston"):
        assert page.diagnostics[name][-1] == obs.landmarks[name].confidence
    assert (
        window.monitor.kpis.labels["confidence"].text()
        == f"{min(p.confidence for p in obs.landmarks.values()):.2f}"
    )
    missing = Observation(
        previous.timestamp + 1 / 30, {}, frame_id=previous.frame_id + 1
    )
    result = processor.step(missing)
    window._on_sample(
        np.zeros((390, 620, 3), dtype=np.uint8),
        twin_frame(geo, result["physics"]),
        dict(observation=missing, metrics=result, synthetic=True),
    )
    assert all(
        math.isnan(page.diagnostics[name][-1]) for name in ("pivot", "crank", "piston")
    )
    assert window.monitor.kpis.labels["confidence"].text() == "—"
    window.navigate(1)
    np.testing.assert_allclose(
        page.curves["piston_observed"].getData()[1],
        list(window.state.series["piston_observed"]),
        equal_nan=True,
    )
    processor.close()


def test_evaluation_chart_and_export_use_original_report(window, tmp_path):
    page = window.experiments
    page.seconds.setValue(2)
    page.run_evaluation()
    wait_until(lambda: page.last_result is not None and not page.busy)
    legend = page.result_chart.getPlotItem().legend
    assert [label.text for _, label in legend.items] == ["MAE", "RMSE", "P95"]
    for key, positions, values in page.result_bars:
        assert values == [
            m[key]
            for m in page.last_result["methods"].values()
            if m.get(key) is not None
        ]
    destination = tmp_path / "export.csv"
    source = page.export_results_to(destination)
    assert destination.read_bytes() == Path(source).read_bytes()


@pytest.mark.parametrize("theta", [float("nan"), float("inf")])
def test_twin_nonfinite_estimate_never_draws_pose(theta):
    geo = Geometry()
    image = twin_frame(geo, Estimate(0, theta=theta, status="TRACKING"))
    missing = twin_frame(geo, Estimate(0, theta=None, status="TRACKING"))
    np.testing.assert_array_equal(image, missing)


@pytest.mark.parametrize("size", [(1366, 768), (1600, 900), (1920, 1080)])
def test_v4_nested_pages_fit_at_target_sizes(window, app, size):
    window.resize(*size)
    for index, page in [(1, window.analysis), (3, window.settings)]:
        window.navigate(index)
        for tab in range(page.tabs.count()):
            page.tabs.setCurrentIndex(tab)
            app.processEvents()
            assert window.size().toTuple() == size
            assert not page.tabs.currentWidget().visibleRegion().isEmpty()


@pytest.mark.parametrize("size", [(1366, 768), (1600, 900)])
def test_monitoring_redesign_prioritizes_viewports(window, app, size):
    window.resize(*size)
    window.navigate(0)
    app.processEvents()
    monitor = window.monitor
    left, right = monitor.media_splitter.sizes()
    assert 0.55 <= left / (left + right) <= 0.57
    assert monitor.camera.width() >= 580 and monitor.camera.height() >= 320
    assert monitor.twin.width() >= 450 and monitor.twin.height() >= 320
    assert (
        monitor.kpis.mapTo(window, QPoint(0, 0)).y()
        > monitor.camera.mapTo(window, monitor.camera.rect().bottomLeft()).y()
    )
    assert sum(card.isVisible() for card in monitor.kpis.cards.values()) == 6


def test_session_details_and_full_path_copy(window, tmp_path, monkeypatch):
    from types import SimpleNamespace
    from PySide6.QtWidgets import QApplication

    copied = []
    monkeypatch.setattr(
        QApplication, "clipboard", lambda: SimpleNamespace(setText=copied.append)
    )
    page = window.experiments
    path = str(tmp_path / "session.csv")
    row = page.add_session("video", "color", path)
    page.update_session(row, 42)
    assert "42" in page.history_summary.text()
    assert "Video" in page.session_details.text()
    page.copy_session_button.click()
    assert copied[-1] == path
    page.last_output = str(tmp_path)
    page.copy_output_button.setEnabled(True)
    page.copy_output_button.click()
    assert copied[-1] == str(tmp_path.resolve())
    settings = window.settings
    settings.source_mode.setCurrentIndex(settings.source_mode.findData("camera"))
    settings.detector_mode.setCurrentIndex(settings.detector_mode.findData("yolo"))
    assert settings.weights_path.isEnabled()
    assert "YOLO" in settings.config_summary.text()
    settings.set_locked(True)
    assert "dừng phiên" in settings.activation_note.text()
