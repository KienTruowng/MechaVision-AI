"""Kiểm tra đường đi dữ liệu và cảnh báo Qt; bỏ qua nếu chưa cài nhóm gui."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
pytest.importorskip('pyqtgraph')
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from mechavision import gui


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    widget = gui.MainWindow()
    yield widget
    if widget.worker and widget.worker.isRunning():
        widget.stop()
        assert widget.worker.wait(3000)
    widget.close()
    app.processEvents()


def test_translated_source_starts_real_simulation_worker(window, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    errors = []
    monkeypatch.setattr(gui, '_message', lambda *args: errors.append(args))
    window.start()
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    window.worker.sample.connect(lambda *args: loop.quit() if len(window.timestamps) >= 4 else None)
    timer.start(5000)
    loop.exec()
    timer.stop()
    window.stop()
    assert window.worker.wait(3000)
    QApplication.processEvents()
    assert not errors
    assert len(window.timestamps) >= 4
    assert window.worker.mode == 'simulation'
    assert window.worker.detector_name == 'color'
    assert list((tmp_path / 'outputs').glob('session_*.csv'))
    assert 'MÔ PHỎNG' in window.banner.text()


def test_camera_without_calibration_has_vietnamese_warning(window, monkeypatch):
    messages = []
    monkeypatch.setattr(gui, '_message', lambda *args: messages.append(args))
    window.source_mode.setCurrentIndex(window.source_mode.findData('camera'))
    window.geom_path.setText('missing/calibration.json')
    window.start()
    assert window.worker is None
    assert messages[0][1] == 'Cần hiệu chuẩn'


def test_export_dialog_preserves_csv_option_values(window, tmp_path):
    dialog = window.angle_plot.scene().exportDialog
    dialog.show(window.angle_plot.getPlotItem())
    formats = dialog.ui.formatList
    for index in range(formats.count()):
        if formats.item(index).expClass.__name__ == 'CSVExporter':
            formats.setCurrentRow(index)
            break
    else:
        pytest.fail('Không có bộ xuất CSV')
    params = dialog.currentExporter.parameters()
    assert params.child('separator').value() == 'comma'
    assert params.child('separator').opts['title'] == 'Dấu phân cách'
    assert params.child('separator').opts['limits']['Dấu phẩy'] == 'comma'
    assert dialog.ui.itemTree.topLevelItem(0).text(0) == 'Toàn bộ vùng đồ thị'
    window.angle_raw_curve.setData([0., 1.], [10., 20.])
    target = tmp_path / 'biểu đồ.csv'
    dialog.currentExporter.export(str(target))
    import csv
    with target.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ['Góc từ điểm đặc trưng_x', 'Góc từ điểm đặc trưng_y']
    assert [float(value) for value in rows[2]] == [1., 20.]
    dialog.close()
