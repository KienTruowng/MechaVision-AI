# Build validation record

- Automated test suite: **21 passed** in the project build environment (Python 3.13, NumPy and OpenCV installed).
- Python syntax: `python -m compileall -q src` passed.
- CLI simulation: `python -m mechavision simulate --seconds 4` passed.
- CLI synthetic ablation: `python -m mechavision evaluate --seconds 24 --fps 30 --seed 42` passed.
- ArUco marker sheet generation: `python -m mechavision markers` passed.
- Paired replay of real-format recorded observations against independent reference-angle CSV format: exercised with **synthetic test fixture**; this validates code logic but **not real-engine accuracy**.

## Not verified in this environment

- **Qt desktop GUI** execution: PySide6 and PyQtGraph were unavailable. An attempted install failed because the build environment could not access the package index; source is included, but must be validated on Windows.
- **YOLO custom training/inference**: no real mechanical recordings, annotated dataset, model weights or Ultralytics installation were available. Scripts and integration code are provided for running on the user's machine.
- **Physical engine geometry**, real-camera calibration, absolute measurement accuracy, physical FPS / p95 latency and RTX 3050 Ti performance: not measurable remotely without the physical rig.

Do not treat the simulator's benchmark results as a claim about the real mechanism or industrial machine monitoring.
