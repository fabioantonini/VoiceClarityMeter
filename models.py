from datetime import datetime

from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Call data model for storing call history in database
class CallRecord(db.Model):
    __tablename__ = 'call_records'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.String(255), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Float, default=0)
    from_address = db.Column(db.String(255), nullable=True)
    to_address = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='active')
    
    # Quality metrics
    avg_mos = db.Column(db.Float, default=0)
    min_mos = db.Column(db.Float, default=5.0)
    max_mos = db.Column(db.Float, default=1.0)
    packet_loss_rate = db.Column(db.Float, default=0)
    avg_jitter = db.Column(db.Float, default=0)
    avg_delay = db.Column(db.Float, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# Quality metrics model for storing detailed metrics per call
class QualityMetric(db.Model):
    __tablename__ = 'quality_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.String(255), db.ForeignKey('call_records.call_id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # Metrics
    mos_score = db.Column(db.Float, nullable=False)
    packet_loss_rate = db.Column(db.Float, default=0)
    jitter = db.Column(db.Float, default=0)
    delay = db.Column(db.Float, default=0)
    packets_received = db.Column(db.Integer, default=0)
    packets_lost = db.Column(db.Integer, default=0)
    
    # Relationships
    call_record = db.relationship('CallRecord', backref='quality_metrics')