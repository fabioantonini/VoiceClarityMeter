"""Simple database models for VoIP Quality Monitor"""
from datetime import datetime
import json
import os

class CallRecord:
    """Simple call record class for file-based storage"""
    def __init__(self, call_id, start_time=None, end_time=None, duration=0, 
                 from_address=None, to_address=None, status='active'):
        self.call_id = call_id
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.duration = duration
        self.from_address = from_address
        self.to_address = to_address
        self.status = status
        self.avg_mos = 0
        self.min_mos = 5.0
        self.max_mos = 1.0
        self.packet_loss_rate = 0
        self.avg_jitter = 0
        self.avg_delay = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {
            'call_id': self.call_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'status': self.status,
            'avg_mos': self.avg_mos,
            'min_mos': self.min_mos,
            'max_mos': self.max_mos,
            'packet_loss_rate': self.packet_loss_rate,
            'avg_jitter': self.avg_jitter,
            'avg_delay': self.avg_delay,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        record = cls(data['call_id'])
        record.start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
        record.end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        record.duration = data.get('duration', 0)
        record.from_address = data.get('from_address')
        record.to_address = data.get('to_address')
        record.status = data.get('status', 'active')
        record.avg_mos = data.get('avg_mos', 0)
        record.min_mos = data.get('min_mos', 5.0)
        record.max_mos = data.get('max_mos', 1.0)
        record.packet_loss_rate = data.get('packet_loss_rate', 0)
        record.avg_jitter = data.get('avg_jitter', 0)
        record.avg_delay = data.get('avg_delay', 0)
        record.created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        record.updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        return record

class QualityMetric:
    """Simple quality metric class"""
    def __init__(self, call_id, mos_score, packet_loss_rate=0, jitter=0, 
                 delay=0, packets_received=0, packets_lost=0):
        self.call_id = call_id
        self.timestamp = datetime.now()
        self.mos_score = mos_score
        self.packet_loss_rate = packet_loss_rate
        self.jitter = jitter
        self.delay = delay
        self.packets_received = packets_received
        self.packets_lost = packets_lost
    
    def to_dict(self):
        return {
            'call_id': self.call_id,
            'timestamp': self.timestamp.isoformat(),
            'mos_score': self.mos_score,
            'packet_loss_rate': self.packet_loss_rate,
            'jitter': self.jitter,
            'delay': self.delay,
            'packets_received': self.packets_received,
            'packets_lost': self.packets_lost
        }