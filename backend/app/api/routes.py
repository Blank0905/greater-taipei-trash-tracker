from flask import Blueprint, jsonify, request
from app.db import get_db_connection

bp = Blueprint('stations', __name__, url_prefix='/api/stations')

@bp.route('/', methods=['GET'])
def get_all_stations():
    """範例：取得前 10 筆站點"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT station_id, station_name, latitude, longitude, arrive_time FROM stations LIMIT 10"
            cursor.execute(sql)
            stations = cursor.fetchall()
            
            for s in stations:
                if s['arrive_time']:
                    s['arrive_time'] = str(s['arrive_time'])
                    
            return jsonify({'status': 'success', 'data': stations})
    finally:
        conn.close()

@bp.route('/search', methods=['GET'])
def search_nearby():
    """
    進階範例：給定經緯度算距離，並找出附近 2 公里內的站點
    參數: lat, lng, radius (預設 2km)
    """
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', type=float, default=2.0)

    if lat is None or lng is None:
        return jsonify({'status': 'error', 'message': 'Missing lat or lng'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 這是專業的 Haversine 距離計算 SQL
            # 6371 是地球半徑 (公里)
            sql = """
                SELECT *, (
                    6371 * acos (
                        cos ( radians(%s) )
                        * cos( radians( latitude ) )
                        * cos( radians( longitude ) - radians(%s) )
                        + sin ( radians(%s) )
                        * sin( radians( latitude ) )
                    )
                ) AS distance
                FROM stations
                HAVING distance < %s
                ORDER BY distance ASC
                LIMIT 20
            """
            cursor.execute(sql, (lat, lng, lat, radius))
            results = cursor.fetchall()

            for r in results:
                if r['arrive_time']: r['arrive_time'] = str(r['arrive_time'])
                if r['leave_time']: r['leave_time'] = str(r['leave_time'])
                r['distance'] = round(float(r['distance']), 3) # 轉成公里並取到小數三位

            return jsonify({'status': 'success', 'count': len(results), 'data': results})
    finally:
        conn.close()
