from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'developer', 'admin'), default='user')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 關聯
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    fav_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.station_id', ondelete='CASCADE'), nullable=False)
    alias = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    noti_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.station_id', ondelete='CASCADE'), nullable=False)
    remind_before_mins = db.Column(db.Integer, default=10)
    notify_garbage = db.Column(db.Boolean, default=True)
    notify_recycling = db.Column(db.Boolean, default=True)
    notify_foodscraps = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    device_token = db.Column(db.String(255))
    push_method = db.Column(db.Enum('web', 'line', 'email'), default='web')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
