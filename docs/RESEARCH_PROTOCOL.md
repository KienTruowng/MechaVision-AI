# Research protocol (bản thiết kế học thuật)

## Question and falsifiable hypotheses

**RQ:** Does adding physically meaningful slider-crank measurement constraints to a temporal visual estimator improve angle reconstruction on *previously unseen* real-video sessions with noise, partial occlusions and varying speed?

- H1: The physics-informed EKF reduces angular MAE/RMSE vs the same EKF using crank landmarks alone on held-out data.
- H2: With a temporary loss of crank observations but retained piston observations, the method improves valid-state coverage without a disproportionate rise in error.
- H3: Added constraints should not substantially increase end-to-end inference latency; measure rather than assume.

**Null hypotheses:** no improvement or a worse tradeoff at the same conditions. Report negative results honestly.

## Mathematical model

For an ideal offset slider crank with measured radius r, rod length l and slider rail offset e, piston joint coordinate along the positive axis is

\[x(\theta)=r\cos\theta+\sqrt{l^2-(e-r\sin\theta)^2}.\]

The state \(s_t=[\theta_t,\omega_t]^T\) evolves under a constant-velocity local model plus Gaussian acceleration noise:

\[s_{t+1}=\begin{bmatrix}1&\Delta t\\0&1\end{bmatrix}s_t+w_t.\]

The visual observation function predicts crank-pin image location and, in the constrained model, piston-rod joint image location from the same state. EKF prediction, innovation, gating, and Joseph-form covariance update are implemented in `estimators.py`. The temporal baseline uses *the same process model, noise choices and crank measurements*, but excludes the piston measurement. This isolates the additional geometry-derived information. The raw baseline infers crank angle from a detected rotating pin relative to the pivot.

**Important distinction:** using a known geometric observation function is not automatically a newly invented optimization algorithm. The academic contribution must be the validated adaptation to the chosen constrained-vision problem and evidence from proper controlled studies.

## Experimental design

- Use 3+ distinct *acquisition sessions* under each condition, varied by start angle/speed and light levels. Keep train/val/test session groups disjoint.
- Conditions: nominal, illumination change, varying speed + reversal, occluded crank with piston visible, occluded piston with crank visible, simultaneous occlusion (abstention test).
- Collect true or independently measured crank angle and uncertainty per selected frame. Do not rely on synthetic simulator truth in real experiments.
- Collect independent pixel annotations for the pivot, crank pin and rod/piston joint to assess keypoint error; report AI detection precision and keypoint displacement separately from state estimation.
- Measure angle MAE/RMSE/p95, valid-prediction coverage, false valid predictions under occlusion, latency (camera acquisition → result), p95 latency, FPS, memory and VRAM use. Optional confidence calibration analysis.
- Distinguish angular errors modulo 360° from **unwrapped** cycle counting errors. The former cannot validate number of revolutions.
- Report the same measurement stream through all three estimators (paired experiment), with bootstrap confidence intervals by **session**, not independent adjacent frame resampling.
- Tune thresholds and filter parameters using training/validation data only, freeze before final test.

## Explicit limitations and failure cases

- Offset slider–crank model applies only if kinematics genuinely match the mechanism. Analyze gears, nonplanar parts and piston joint location before building a final scientific claim.
- RGB camera projection needs calibration; 2D near-orthographic approximation is not generally valid under oblique viewpoints. A homography is a possible extension.
- Crankpin occlusion near dead center may make piston-based angle correction weak or ambiguous. A multi-hypothesis tracker is a stretch goal, not promised behavior.
- Stopping or reversing a manually driven engine is **not** mechanical damage. This implementation provides consistency measurements and tracking quality; it does not diagnose industrial faults.
- Synthetic results are smoke tests only and never evidence that the trained detector or physical experiment succeeds.

## Milestones

1. Verify physically visible, unambiguous points and geometry from user hardware; reject invalid geometry.
2. Capture data and establish independent labels/measurement protocol.
3. Build and train custom keypoint network; evaluate against OpenCV/ArUco reference when appropriate.
4. Evaluate temporal EKF and physics EKF on identical saved observations.
5. Add robust real-time software, dashboard and session logging; benchmark laptop performance.
6. Repeat experiments, analyze errors and compose the thesis with reproducible scripts and limitations.
