from app import db

class StationSchedule(db.Model):
    __tablename__ = 'station_schedules'
    
    schedule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.station_id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.SmallInteger, index=True, nullable=False) # 0=日, 1=一, 2=二, ...
    collects_garbage = db.Column(db.Boolean, default=False)
    collects_recycling = db.Column(db.Boolean, default=False)
    collects_foodscraps = db.Column(db.Boolean, default=False)
