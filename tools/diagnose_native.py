"""Thông tin chẩn đoán native; không thay biến môi trường hoặc backend."""
import os
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

print(sys.version, platform.platform(), flush=True)
for name in (
    'numpy',
    'opencv-contrib-python',
    'opencv-contrib-python-headless',
    'PySide6',
    'shiboken6',
    'pyqtgraph',
    'Pillow',
    'pytest',
):
    try:
        print(name, version(name), flush=True)
    except PackageNotFoundError:
        print(name, 'not installed', flush=True)
for key in ('QT_QPA_PLATFORM', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'DISPLAY', 'LD_LIBRARY_PATH'):
    print(key, os.environ.get(key), flush=True)
# Hai tiến trình độc lập: so sánh Qt đơn lẻ và thứ tự import giống collection test.
for prefix in ('', 'import cv2; import numpy;'):
    code = prefix + '''
from PySide6.QtCore import QLibraryInfo, qVersion
from PySide6.QtWidgets import QApplication
import os
print('Qt', qVersion(), 'plugins', QLibraryInfo.path(QLibraryInfo.PluginsPath), flush=True)
print('platform plugin env', os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH'), flush=True)
app = QApplication([])
print('active platform', app.platformName(), flush=True)
'''
    print('Probe:', prefix or 'Qt only', flush=True)
    result = subprocess.run([sys.executable, '-X', 'faulthandler', '-c', code], timeout=60)
    print('Probe returncode:', result.returncode, flush=True)
import cv2
import numpy as np
print(cv2.getBuildInformation(), flush=True)
np.show_config()
