# MechaVision AI

**Real-Time Physics-Constrained Visual State Estimation of a Slider–Crank Mechanism**

A research-oriented Python application combining **OpenCV**, **custom YOLO pose keypoints**, **nonlinear Extended Kalman Filtering**, **planar kinematics**, **reproducible evaluation**, and a **PySide6/PyQtGraph desktop dashboard**. Developed as a technically grounded graduation-thesis software prototype.

> **Important:** The source code implements the complete software workflow. It includes a working mathematical simulator, webcam/video processing, traditional marker detectors, YOLO pose training/inference adapters, manual annotation, session-disjoint dataset preparation, calibration, real/synthetic benchmarking, dashboard, and unit tests. **A trained keypoint model for your specific engine is NOT included:** it cannot be produced truthfully without photographs/videos and labels from that engine. No real-world accuracy, FPS or industrial fault-detection claim is made. The GUI code is included but couldn't be runtime-verified in the build environment, where Qt packages are unavailable.

## Scientific problem

Estimate the unwrapped crankshaft angle `theta(t)`, angular velocity `omega(t)`, and piston joint position in real time under visual noise, temporary occlusion and irregular manually-driven motion. Compare **the same observations** across three methods:

| Method | Measurements | What it establishes |
|---|---|---|
| Direct visual baseline | Crank pin + pivot | Unfiltered point-based angle |
| Temporal EKF baseline | Crank pin + time | Effect of temporal filtering |
| Physics-constrained EKF | Crank pin + piston joint + time | Effect of measured slider–crank geometric relationship |

The EKF is a known algorithm, not a claimed original invention. The thesis contribution to be evaluated is the application and validation of physically constrained fusion for this visual measurement problem. Negative or mixed results must be reported, not concealed.

## Installation — Windows 11, Python 3.12

Unzip the project and open PowerShell **inside the `MechaVision-AI` directory**:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.venv\Scripts\python.exe -m mechavision gui
```

Or double-click **`run_windows.bat`** after installation. For actual YOLO training/inference, also install:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[train]"
```

The `train` extra may install CPU-only PyTorch. For NVIDIA RTX 3050 Ti 4 GB, follow the official [PyTorch Windows installation instructions](https://pytorch.org/get-started/locally/) to install a CUDA-compatible build. Start with YOLO-nano, image size 640, batch size **4**, lower to **2** if VRAM is insufficient. GPU speed has **not** been measured here.

## 1. Run the full desktop dashboard immediately

```powershell
.venv\Scripts\python.exe -m mechavision gui
```

Choose **`simulation` → `Start analysis`**. It shows an explicitly labeled *synthetic* rotating mechanism, observation overlays, a 2D kinematic twin, angle, RPM, model disagreement and two live plots. Every session is logged to `outputs/session_*.csv`.

Simulation/algorithm comparison without GUI:

```powershell
.venv\Scripts\python.exe -m mechavision simulate --seconds 12
.venv\Scripts\python.exe -m mechavision evaluate --seconds 24 --fps 30 --noise 3 --out outputs/ablation
.venv\Scripts\python.exe -m pytest -q
```

**Simulation demonstrates functioning code; it does not validate the physical LEGO mechanism.**

## 2. Connect a real camera (works before AI training)

Two physically-grounded marker options are available:

- **Colored dots:** red = fixed crank pivot, green = crank pin, blue = connecting-rod joint on the piston. Choose `color` detector. The physical centers of dots must actually match the modeled joint centers.
- **ArUco tags:** generate a printable sheet with IDs `0` pivot, `1` crank, `2` piston. Choose `aruco` detector. Physical center offsets are **not automatically corrected**.

```powershell
.venv\Scripts\python.exe -m mechavision markers --out assets/aruco_markers.png
.venv\Scripts\python.exe -m mechavision calibrate --source 0 --out configs/geometry.json
.venv\Scripts\python.exe -m mechavision live --source 0 --detector color --geometry configs/geometry.json
```

Calibrate in four clicks: **(1)** crank pivot `O`, **(2)** crank pin `C`, **(3)** real piston/rod joint `S`, **(4)** a point in the positive slider-axis direction. Press Enter to confirm. Repeat with the real camera stable and approximately perpendicular to the motion plane. The calibration rejects incompatible rigid slider–crank geometry. The system is **not appropriate** for an unrelated mechanism or invisible piston joint without changing its physical measurement model.

You can alternatively select **`camera` / `video`** in the GUI, provide `configs/geometry.json`, choose `color`, `aruco`, or `yolo`, and start the session.

## 3. Collect data and train a real custom YOLO pose model

Capture at least three **independent** recordings; preferably many more with different lighting, hand-cranking speeds, stops, reversals, and occlusions:

```powershell
.venv\Scripts\python.exe -m mechavision record --out data/raw/session01.mp4 --seconds 30
.venv\Scripts\python.exe -m mechavision record --out data/raw/session02.mp4 --seconds 30
.venv\Scripts\python.exe -m mechavision record --out data/raw/session03.mp4 --seconds 30
```

Extract images, label them, and split the dataset **by recording session** (not random adjacent frames):

```powershell
.venv\Scripts\python.exe -m mechavision extract --video data/raw/session01.mp4 --session session01 --stride 8
.venv\Scripts\python.exe -m mechavision extract --video data/raw/session02.mp4 --session session02 --stride 8
.venv\Scripts\python.exe -m mechavision extract --video data/raw/session03.mp4 --session session03 --stride 8
.venv\Scripts\python.exe -m mechavision annotate --folder data/labeled/session01
.venv\Scripts\python.exe -m mechavision annotate --folder data/labeled/session02
.venv\Scripts\python.exe -m mechavision annotate --folder data/labeled/session03
.venv\Scripts\python.exe -m mechavision split --root data/labeled --out data/pose_dataset
```

Label three physical points in order: `pivot`, `crank`, `piston`. **Left click** to mark the current point, **S** to skip an occluded point, **R** to reset and **Enter** to save an annotated frame. Completely unobservable frames are skipped. Use consistent annotation rules; *do not label inferred or invisible points as observed*.

Train and validate (network access may be needed to download the `yolo11n-pose.pt` pretrained initialization):

```powershell
.venv\Scripts\python.exe -m mechavision train --data data/pose_dataset/data.yaml --model yolo11n-pose.pt --epochs 80 --batch 4 --device 0
.venv\Scripts\python.exe -m mechavision validate --data data/pose_dataset/data.yaml --weights runs/mechavision/pose/weights/best.pt --split test --device 0
.venv\Scripts\python.exe -m mechavision keypoint-eval --data data/pose_dataset --weights runs/mechavision/pose/weights/best.pt --split test --device 0
```

The path of `best.pt` can vary when Ultralytics increments run folders. Check the actual output. For CPU-only usage use `--device cpu`. With a trained checkpoint, camera inference is:

```powershell
.venv\Scripts\python.exe -m mechavision live --source 0 --detector yolo --weights runs/mechavision/pose/weights/best.pt --geometry configs/geometry.json --device 0
```

A generic human pose model **cannot** detect these custom mechanical keypoints without fine-tuning.

## 4. Rigorous real-world experiments

Gather independent ground truth using manual reference measurements or a physical encoder, **not the same EKF**. Reference CSV example in `samples/reference_angles_TEMPLATE.csv`:

```csv
frame,theta_deg
1,17.5
2,22.2
3,27.1
```

Run all three estimators against **the identical recorded detections**, with their parameter choices frozen before final test:

```powershell
.venv\Scripts\python.exe -m mechavision real-ablation --session outputs/live_session.csv --ground-truth data/reference_angles.csv --geometry configs/geometry.json --out outputs/real_ablation
```

This creates `summary.json` and `real_ablation.csv` with per-method MAE, RMSE, p95 angle error and valid-coverage. Separate metrics for crank occlusion are included when applicable. Errors are wrapped modulo 360 degrees; counting full revolutions needs additional analysis. See `docs/RESEARCH_PROTOCOL.md`.

A single-estimator angle evaluation is also available:

```powershell
.venv\Scripts\python.exe -m mechavision evaluate-real --session outputs/live_session.csv --ground-truth data/reference_angles.csv --out outputs/real_evaluation.json
```

## Architecture

```text
Camera/video ----> color / ArUco / trained YOLO detector --+
                                                             |
Synthetic labeled source (clearly identified) ---------------+---> Observation
                                                                      |
                                              +-----------------------+---------------------+
                                              |                       |                     |
                                          Raw Visual             Temporal EKF         Physics EKF
                                              |                       |                     |
                                              +----------- Compare / confidence -----------+
                                                                           |
                                        Desktop dashboard / Digital Twin / CSV logs / evaluation
```

- `src/mechavision/geometry.py` — slider–crank with optional rail offset, analytic derivative, camera-projected coordinates.
- `estimators.py` — direct baseline and nonlinear EKF; observation-dependent covariance, outlier gating, uncertainty-based abstention.
- `detection.py`, `acquisition.py` — real camera/video observation adapters.
- `dataset.py`, `train.py` — image extraction, manual labeling, session split, custom pose training/validation.
- `real_ablation.py`, `real_evaluation.py`, `evaluation.py` — paired real-video and synthetic evaluation.
- `gui.py`, `processing.py`, `render.py` — Qt app, streaming pipeline, visualization.
- `tests/` — automatic tests for geometry, tracking, camera markers, data handling, and evaluation.

## Scientific and practical limitations

1. The actual LEGO mechanism must be checked to confirm it matches an **ideal planar slider–crank**, its visible keypoints match the modeled joints, and the projected geometry is meaningful. **Without this, the real-mechanism result is not validated.**
2. Inference on real footage is not demonstrated here without a trained engine-specific checkpoint; using `color`/`aruco` is a valid **baseline**, not a substitute for Deep Learning results.
3. The two-state EKF assumes a locally constant angular velocity with acceleration process noise; long occlusion can cause phase aliasing, at which point the system should report loss of confidence.
4. Real-world absolute measurement, latency and robustness claims require controlled experiments on the target laptop. Hand-driven stops, speed changes and reversals are **normal**, not mechanical faults.
5. This is a **research-grade runnable codebase**, not a certified industrial condition-monitoring or fault-detection product.

## Publishing to GitHub

The ZIP is ready to work locally. To create your own `KienTruowng/MechaVision-AI` repository from Windows, install [Git](https://git-scm.com/downloads/win) and [GitHub CLI](https://cli.github.com/), run `gh auth login`, then use `tools/publish_github.ps1`. The script creates a **private** repository by default, commits all tracked code, and pushes `main` without uploading datasets, models, local configurations, secrets, or generated experiment output (see `.gitignore`).

License: MIT. Check licensing requirements of the underlying frameworks and model weights separately.
