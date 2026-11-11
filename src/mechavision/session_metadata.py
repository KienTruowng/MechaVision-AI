"""Metadata bổ sung; không thay schema CSV hoặc kết quả đánh giá."""
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
from collections import Counter


class SessionMetadata:
    def __init__(self, log_path, mode, source, detector, device, geometry):
        self.path = Path(log_path).with_suffix('.metadata.json')
        self.counts = Counter()
        self.data = dict(schema_version=1, source_mode=mode, source=str(source),
                         detector=detector, device=device, geometry=asdict(geometry),
                         classification='simulation' if mode=='simulation' else 'unverified_capture',
                         accuracy_status='unavailable_without_independent_reference',
                         started_utc=datetime.now(timezone.utc).isoformat(),
                         units=dict(position='pixel', angle='radian', time='second'),
                         frames=0, state='running', latency_ms=None)
        self.save()

    def record(self, obs, estimate):
        self.data['frames'] += 1
        self.data.setdefault('first_timestamp_s', obs.timestamp)
        self.data['last_timestamp_s'] = obs.timestamp
        self.counts[estimate.status] += 1

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.json.tmp')
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        temp.replace(self.path)

    def finish(self, state, error=None):
        self.data.update(state=state, error=error, tracking_counts=dict(self.counts),
                         ended_utc=datetime.now(timezone.utc).isoformat())
        self.save()
