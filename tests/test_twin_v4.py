"""Kiểm tra hợp đồng hình học của bản vẽ; các tư thế là fixture kiểm thử."""

import math
import cv2
import numpy as np
import pytest

from mechavision.geometry import Geometry
from mechavision.render import twin_frame
from mechavision.types import Estimate


@pytest.mark.parametrize("size", [(500, 260), (620, 390), (800, 450)])
@pytest.mark.parametrize("offset", [-80, 0, 80])
def test_joint_centers_keep_uniform_kinematic_scale(monkeypatch, size, offset):
    geometry = Geometry(rod_px=200, slider_offset_px=offset)
    previous = None
    original = cv2.circle
    captured = []

    def record(image, center, radius, *args, **kwargs):
        if radius == 7:
            captured.append(center)
        return original(image, center, radius, *args, **kwargs)

    monkeypatch.setattr(cv2, "circle", record)
    for angle in [.4, 2.1, 4.3]:
        captured.clear()
        output = twin_frame(geometry, Estimate(3, theta=angle, status="TRACKING"), *size)
        assert output.shape == (size[1], size[0], 3)
        assert len(captured) == 6
        origin, crank, piston = np.asarray(captured)[::2]
        crank_length = np.linalg.norm(crank - origin)
        rod_length = np.linalg.norm(piston - crank)
        assert rod_length / crank_length == pytest.approx(geometry.rod_px / geometry.radius_px, rel=.045)
        assert all(10 <= x < size[0] - 10 and 30 <= y < size[1] - 30 for x, y in [origin, crank, piston])
        if previous is not None:
            assert np.array_equal(origin, previous[0])
            assert piston[1] == previous[1]
            assert crank_length == pytest.approx(previous[2], abs=1.5)
        previous = origin, piston[1], crank_length


@pytest.mark.parametrize("status,angle", [("LOST", .3), ("UNINITIALIZED", 2), ("TRACKING", float("nan")), ("TRACKING", float("inf"))])
def test_invalid_estimates_never_draw_or_advance_mechanism(status, angle):
    geo = Geometry()
    first = twin_frame(geo, Estimate(1, theta=angle, status=status))
    second = twin_frame(geo, Estimate(999, theta=None, status=status))
    np.testing.assert_array_equal(first, second)


def test_render_cache_is_not_mutated_by_output_or_time():
    geo = Geometry()
    estimate = Estimate(0, theta=math.pi / 3, status="TRACKING")
    expected = twin_frame(geo, estimate)
    corrupted = twin_frame(geo, estimate)
    corrupted[:] = 255
    estimate.timestamp = 999
    np.testing.assert_array_equal(twin_frame(geo, estimate), expected)
