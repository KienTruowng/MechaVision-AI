import math
import numpy as np
import pytest
from mechavision.geometry import Geometry,wrap_angle,nearest_angle


def test_slider_rod_length_and_offset():
    geo=Geometry(radius_px=40,rod_px=190,slider_offset_px=17,axis_deg=37)
    for theta in np.linspace(-4*math.pi,4*math.pi,200):
        p=geo.points(theta)
        assert np.linalg.norm(p['piston']-p['crank'])==pytest.approx(geo.rod_px,abs=1e-8)
        assert geo.local(p['piston'])[1]==pytest.approx(geo.slider_offset_px,abs=1e-8)
        assert wrap_angle(geo.theta_from_crank(p['crank'])-theta)==pytest.approx(0,abs=1e-8)


def test_analytical_jacobian_matches_finite_differences():
    geo=Geometry(radius_px=55,rod_px=210,slider_offset_px=-12)
    for t in np.linspace(-math.pi,math.pi,40):
        eps=1e-5
        numerical=(geo.slider_x(t+eps)-geo.slider_x(t-eps))/(2*eps)
        assert geo.slider_dx_dtheta(t)==pytest.approx(numerical,abs=1e-5)


def test_calibration_recovers_geometry():
    geo=Geometry(radius_px=47,rod_px=198,origin_x=350,origin_y=170,axis_deg=33,slider_offset_px=16)
    points=geo.points(.8)
    direction=geo.image(120,0)
    fitted=Geometry.from_landmarks(points['pivot'],points['crank'],points['piston'],direction)
    assert fitted.radius_px==pytest.approx(geo.radius_px)
    assert fitted.rod_px==pytest.approx(geo.rod_px)
    assert fitted.axis_deg==pytest.approx(geo.axis_deg)
    assert fitted.slider_offset_px==pytest.approx(geo.slider_offset_px)


def test_geometry_json_roundtrip(tmp_path):
    geo=Geometry(slider_offset_px=23,rod_px=201)
    p=tmp_path/'geometry.json';geo.to_json(p)
    assert Geometry.from_json(p)==geo


def test_nearest_angle_unwrap():
    assert nearest_angle(-math.pi+.03,math.pi-.03)==pytest.approx(math.pi+.03)
    with pytest.raises(ValueError):Geometry(radius_px=80,rod_px=50)
