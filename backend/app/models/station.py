from app import db

class Area(db.Model):
    __tablename__ = 'areas'
    
    areas_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city = db.Column(db.Enum('台北市', '新北市', '基隆市'), nullable=False)
    district = db.Column(db.String(20))
    village = db.Column(db.String(50))

    # 關聯
    routes = db.relationship('Route', backref='area', lazy=True)
    stations = db.relationship('Station', backref='area', lazy=True)

class BagRegulation(db.Model):
    __tablename__ = 'bag_regulations'
    
    reg_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city = db.Column(db.Enum('台北市', '新北市'), nullable=False)
    bag_size = db.Column(db.String(20), nullable=False)
    volume_liters = db.Column(db.Numeric(5, 1))
    price = db.Column(db.Numeric(5, 2))
    purchase_locations = db.Column(db.Text)
    notes = db.Column(db.Text)

class Route(db.Model):
    __tablename__ = 'routes'
    
    route_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    areas_id = db.Column(db.Integer, db.ForeignKey('areas.areas_id', ondelete='RESTRICT'), nullable=False)
    route_code = db.Column(db.String(50), index=True)
    route_name = db.Column(db.String(100), nullable=False)
    car_number = db.Column(db.String(20))
    team = db.Column(db.String(50))
    trip_number = db.Column(db.String(20))

    # 關聯
    stations = db.relationship('Station', backref='route', lazy=True)

class Station(db.Model):
    __tablename__ = 'stations'
    
    station_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.route_id', ondelete='CASCADE'), nullable=False)
    areas_id = db.Column(db.Integer, db.ForeignKey('areas.areas_id', ondelete='RESTRICT'), nullable=False)
    station_name = db.Column(db.String(200), nullable=False)
    sequence_order = db.Column(db.Integer)
    longitude = db.Column(db.Numeric(10, 7))
    latitude = db.Column(db.Numeric(10, 7))
    arrive_time = db.Column(db.Time, index=True)
    leave_time = db.Column(db.Time)
    stay_type = db.Column(db.String(20))
    memo = db.Column(db.Text)
    raw_source_id = db.Column(db.String(50))
    
    # 關聯
    schedules = db.relationship('StationSchedule', backref='station', lazy=True, cascade="all, delete-orphan")
