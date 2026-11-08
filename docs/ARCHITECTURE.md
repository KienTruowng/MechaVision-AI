# Software architecture

```text
   physical camera / recorded file              deterministic synthetic source
               |                                           |
               +----------------+--------------------------+
                                |
                           frame + time
                                |
              ArUcoDetector OR YOLOPoseDetector (real)
                     OR synthetic noisy observation
                                |
                    Observation {pivot, crank, piston}
                                |
            +-------------------+----------------------+ 
            |                   |                      |
       RawVisualEstimator   MotionEKF           MotionEKF
            |             (no physics)          (physics on)
            +-------------------+----------------------+
                                |
                   measurements, uncertainty,
                  tracking/predicted/lost status
                                |
            +-------------------+----------------------+
            |                   |                      |
      Qt live dashboard     CSV session logger    offline evaluation
        Digital twin                                 + independent GT
```

- Units: 2D positions **pixels**, timestamps **seconds**, angles **radians**, angular velocity **rad/s**. UI converts to degrees and RPM.
- `Geometry`: physical rigid joints, projection, rail offset, differentiable displacement.
- `MotionEKF`: nonlinear observation update with robust innovation gate and Joseph covariance update. `physics=False` ablates the piston measurement. If the pivot is temporarily missing, uses the last observed pivot, so camera must stay fixed.
- `SessionWriter`: streams CSV; absent measurements remain blank. Simulator truth appears in its own clearly identified column.
- `dataset.py`: custom YOLO pose model expects one object `slider_crank_mechanism` and exactly **three keypoints** in order pivot / crank / piston. No generic human-pose checkpoint assumptions.
- `gui.py`: worker thread owns camera, estimation and logging, emitting frames and measurements to Qt UI. The GUI thread owns charts and painting; model inference does not run in the GUI thread.
- `real_evaluation.py`: joins session prediction and independent ground truth by frame number; report includes valid-coverage denominator. Ground truth data provenance remains user's responsibility.

## Open research/engineering tasks before defense

1. Physical jig and exact point geometry: need real photos/video.
2. Train YOLO Pose on real engine; no engine-specific weights bundled.
3. Build robust manual/encoder reference if possible; verify independent angle labels.
4. Add optional homography and per-camera intrinsic calibration if viewing angle requires it.
5. Confirm EKF uncertainty calibration and model acceleration tuning on held-out sessions.
6. Performance benchmark on target laptop; optional conversion to ONNX if needed.
7. More complete real-data ablation and confidence intervals, not merely synthetic reports.
