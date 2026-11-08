"""One observational pipeline, three independent estimators, CSV logging."""
from __future__ import annotations
import time
import math
from .geometry import Geometry
from .types import Observation
from .estimators import RawVisualEstimator,MotionEKF
from .session import SessionWriter

class Processor:
    def __init__(self,geo:Geometry,log_path:str|None=None):
        self.geo=geo
        self.baseline=RawVisualEstimator(geo)
        self.temporal=MotionEKF(geo,physics=False)
        self.physics=MotionEKF(geo,physics=True)
        self.writer=SessionWriter(log_path) if log_path else None
        self.prev_wall=None
        self.smooth_fps=0.0

    def step(self,obs:Observation):
        tic=time.perf_counter()
        a=self.baseline.update(obs)
        b=self.temporal.update(obs)
        c=self.physics.update(obs)
        if self.writer:self.writer.write(obs,c)
        wall=time.perf_counter()
        if self.prev_wall is not None and wall>self.prev_wall:
            new_fps=1/(wall-self.prev_wall)
            self.smooth_fps=(self.smooth_fps*0.9+new_fps*0.1) if self.smooth_fps else new_fps
        self.prev_wall=wall
        piston=obs.landmarks.get('piston')
        anchor=obs.landmarks.get('pivot')
        observed_x=None
        if piston:
            origin=self.geo.origin if anchor is None else [anchor.x,anchor.y]
            observed_x=float(self.geo.local([piston.x,piston.y],origin)[0])
        predicted_x=self.geo.slider_x(c.theta) if c.theta is not None else None
        return {'baseline':a,'temporal':b,'physics':c,'observed_x':observed_x,
                'predicted_x':predicted_x,'measured_theta':a.theta,
                'fps':self.smooth_fps,'processing_ms':(time.perf_counter()-tic)*1000}

    def close(self):
        if self.writer:self.writer.close()
