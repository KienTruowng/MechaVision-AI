"""Kiểm tra dữ liệu thiếu và ranh giới phiên; không dùng số đo minh họa trong sản phẩm."""

import math
import pytest
from mechavision.dashboard_state import DashboardState
from mechavision.geometry import Geometry
from mechavision.processing import Processor
from mechavision.synthetic import Simulator
from mechavision.types import Observation


def test_missing_observation_is_a_gap_not_zero():
    state = DashboardState()
    processor = Processor(Geometry())
    obs = Observation(1.0, {}, frame_id=1)
    state.append(obs, processor.step(obs))
    assert math.isnan(state.series["raw_angle"][-1])
    assert math.isnan(state.series["physics_angle"][-1])
    assert math.isnan(state.series["physics_rpm"][-1])
    assert state.metrics["physics"].status == "UNINITIALIZED"


def test_reset_does_not_reuse_previous_session_data():
    state = DashboardState()
    geo = Geometry()
    obs = Simulator(geo).step()
    state.append(obs, Processor(geo).step(obs))
    state.reset("camera", "new-session.csv")
    assert state.metrics is None and state.observation is None
    assert state.sample_count == 0
    assert all(not values for values in state.series.values())
    assert state.mode == "camera"


def test_rolling_plot_buffer_keeps_total_session_count(monkeypatch):
    monkeypatch.setattr(DashboardState, "HISTORY_LIMIT", 5)
    state = DashboardState()
    geo = Geometry()
    sim, processor = Simulator(geo), Processor(geo)
    observations = []
    for _ in range(8):
        obs = sim.step()
        observations.append(obs)
        state.append(obs, processor.step(obs))
    assert state.sample_count == 8
    assert len(state.series["time"]) == 5
    assert state.series["time"][0] == pytest.approx(observations[3].timestamp)


def test_temporal_and_physics_curves_keep_original_estimates():
    state = DashboardState()
    geo = Geometry()
    obs = Simulator(geo).step()
    metrics = Processor(geo).step(obs)
    state.append(obs, metrics)
    assert state.series["temporal_angle"][-1] == pytest.approx(
        math.degrees(metrics["temporal"].theta)
    )
    assert state.series["physics_angle"][-1] == pytest.approx(
        math.degrees(metrics["physics"].theta)
    )
    assert state.series["physics_rpm"][-1] == metrics["physics"].rpm
    assert state.series["fps"][-1] == metrics["fps"]


def test_overlay_labels_do_not_overlap_or_change_landmarks():
    from mechavision.render import observation_label_layout
    from mechavision.types import Landmark

    obs = Observation(
        0.0,
        {
            "pivot": Landmark(260, 240),
            "crank": Landmark(210, 270),
            "piston": Landmark(480, 240),
        },
    )
    before = dict(obs.landmarks)
    labels = observation_label_layout((520, 900, 3), obs)
    for index, (_, _, box) in enumerate(labels):
        assert 0 <= box[0] < box[2] <= 900
        assert 0 <= box[1] < box[3] <= 520
        for _, _, other in labels[index + 1 :]:
            assert min(box[2], other[2]) <= max(box[0], other[0]) or min(
                box[3], other[3]
            ) <= max(box[1], other[1])
    assert obs.landmarks == before


@pytest.mark.parametrize("offset", [-200, 200])
def test_twin_keeps_offset_rail_joints_inside_viewport(monkeypatch, offset):
    import cv2
    from mechavision.render import twin_frame
    from mechavision.types import Estimate

    joint_centers = []
    original = cv2.circle

    def record(image, center, radius, *args, **kwargs):
        if radius == 7:
            joint_centers.append(center)
        return original(image, center, radius, *args, **kwargs)

    monkeypatch.setattr(cv2, "circle", record)
    twin_frame(
        Geometry(radius_px=60, rod_px=360, slider_offset_px=offset),
        Estimate(0.0, theta=2.0, status="TRACKING"),
    )
    assert len(joint_centers) == 6
    assert all(20 <= x <= 600 and 80 <= y <= 350 for x, y in joint_centers)
