"""Independent baselines and physics-constrained nonlinear EKF.

State [unwrapped crank angle (rad), angular velocity (rad/s)].
Constant-velocity prediction with high acceleration process noise so hand-cranking
changes speed/reverses. Camera observation is nonlinear. We update on crank
and piston coordinates, weight by measurement confidence, gate gross outliers,
and abstain when uncertainty is too high or no information remains.
"""
from __future__ import annotations
import math
import numpy as np
from .geometry import Geometry, nearest_angle, wrap_angle
from .types import Observation, Estimate


def _point(obs: Observation, name: str) -> np.ndarray | None:
    p=obs.landmarks.get(name)
    return None if p is None else np.array([p.x,p.y],dtype=float)


def _origin(obs: Observation, geo: Geometry) -> np.ndarray:
    # A pivot marker is required or a previously calibrated configured origin.
    # Camera acquisition should not silently assume a correct origin.
    p=_point(obs,"pivot")
    return geo.origin if p is None else p


class RawVisualEstimator:
    """Baseline A: directly infer angle from crank keypoint; no interpolation."""
    def __init__(self,geo:Geometry):
        self.geo=geo
        self.last_theta=None
        self.last_origin=np.array(geo.origin,copy=True)

    def update(self,obs:Observation)->Estimate:
        p=_point(obs,"crank")
        if p is None:
            return Estimate(obs.timestamp,status="LOST")
        pivot=_point(obs,"pivot")
        if pivot is not None:self.last_origin=pivot
        theta=self.geo.theta_from_crank(p,self.last_origin)
        theta=theta if self.last_theta is None else nearest_angle(theta,self.last_theta)
        self.last_theta=theta
        return Estimate(obs.timestamp,theta=theta,status="TRACKING",observation_count=1,measured_crank_theta=theta)


class MotionEKF:
    """Two-state EKF; physics=True uses slider displacement as extra measurement.

    A tracker initialized from crank cannot recover an absolute 2π-turn count after
    a long occlusion, a physical observability limitation. Prediction during
    occlusion is reported as PREDICTED, not TRACKING.
    """
    def __init__(self,geo:Geometry,physics:bool=True,
                 measurement_sigma_px:float=3.0,accel_sigma:float=9.0,
                 max_prediction_sec:float=0.6,max_sigma_deg:float=80.0,
                 gate_sigma:float=4.0):
        self.geo=geo
        self.physics=physics
        self.sigma=measurement_sigma_px
        self.accel=accel_sigma
        self.max_prediction_sec=max_prediction_sec
        self.max_sigma=math.radians(max_sigma_deg)
        self.gate_sigma=gate_sigma
        self.x=None
        self.P=None
        self.last_t=None
        self.last_measured_t=None
        self.last_accepted_crank=None
        self.last_origin=np.array(geo.origin,copy=True)

    def update(self,obs:Observation)->Estimate:
        t=obs.timestamp
        c=_point(obs,"crank")
        p=_point(obs,"piston") if self.physics else None
        pivot=_point(obs,"pivot")
        if pivot is not None:self.last_origin=pivot
        origin=self.last_origin
        if self.x is None:
            if c is None:
                return Estimate(t,status="UNINITIALIZED")
            init=self.geo.theta_from_crank(c,origin)
            self.x=np.array([init,0.0])
            self.P=np.diag([math.radians(9)**2, 4.0**2])
            self.last_t=t
            self.last_measured_t=t
        dt=max(0.0,min(0.25,t-self.last_t))
        self.last_t=t
        # continuous white acceleration process model
        F=np.array([[1.0,dt],[0,1.0]])
        Q=(self.accel**2)*np.array([[dt**4/4,dt**3/2],[dt**3/2,dt**2]])
        self.x=F@self.x
        self.P=F@self.P@F.T+Q
        accepted=0
        rejected=0
        innovations=[]
        measured_crank=None
        discrepancy=None
        if c is not None:
            measured_crank=self.geo.theta_from_crank(c,origin)
            if p is not None:
                discrepancy=float(abs(self.geo.local(p,origin)[0]-self.geo.slider_x(measured_crank)))
        for key,measurement in (("crank",c),("piston",p)):
            if measurement is None:
                continue
            theta=float(self.x[0]);r=self.geo.radius_px
            rad=math.radians(self.geo.axis_deg)
            # image projection of local derivative (x,y)
            def vector_to_image(dx,dy):
                return np.array([math.cos(rad)*dx+math.sin(rad)*dy,
                                 math.sin(rad)*dx-math.cos(rad)*dy])
            if key=="crank":
                h=self.geo.image(r*math.cos(theta),r*math.sin(theta),origin)
                dh=vector_to_image(-r*math.sin(theta),r*math.cos(theta))
            else:
                h=self.geo.image(self.geo.slider_x(theta),self.geo.slider_offset_px,origin)
                dh=vector_to_image(self.geo.slider_dx_dtheta(theta),0.0)
            H=np.column_stack((dh,np.zeros(2)))
            confidence=max(0.08,min(1.0,obs.landmarks[key].confidence))
            R=np.eye(2)*(self.sigma/confidence)**2
            v=measurement-h
            S=H@self.P@H.T+R
            nis=float(v@np.linalg.solve(S,v))
            # The piston-only innovation is locally ambiguous. In a fully
            # initialized filter, EKF linearization follows the prior branch.
            if nis>self.gate_sigma**2:
                rejected+=1
                continue
            K=self.P@H.T@np.linalg.inv(S)
            self.x=self.x+K@v
            I=np.eye(2)
            self.P=(I-K@H)@self.P@(I-K@H).T+K@R@K.T
            self.P=(self.P+self.P.T)*0.5
            innovations.append(float(np.linalg.norm(v)))
            accepted+=1
        if accepted:
            self.last_measured_t=t
        time_since=max(0.0,t-self.last_measured_t)
        sigma=math.sqrt(max(float(self.P[0,0]),0.0))
        if sigma>self.max_sigma or time_since>self.max_prediction_sec:
            status="LOST"
        elif accepted:
            status="TRACKING"
        else:
            status="PREDICTED"
        # Never supply a seemingly valid value after uncertainty timeout.
        return Estimate(t,theta=float(self.x[0]) if status!="LOST" else None,
                        omega=float(self.x[1]) if status!="LOST" else None,
                        sigma_theta=sigma,status=status,observation_count=accepted,
                        rejected_count=rejected,
                        fit_residual_px=float(np.mean(innovations)) if innovations else None,
                        measured_crank_theta=measured_crank,
                        kinematic_discrepancy_px=discrepancy)
