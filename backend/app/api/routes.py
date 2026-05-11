from flask import Blueprint, jsonify
from app.models import Station

# 1. 建立 Blueprint (藍圖)：把它當作是「API 群組」，把相關的 API 打包在一起。
# 這裡設定網址前綴為 /api/stations
bp = Blueprint('stations', __name__, url_prefix='/api/stations')

@bp.route('/', methods=['GET'])
def get_all_stations():
    # 2. 透過 SQLAlchemy 去資料庫撈資料 (先示範抓前 10 筆避免太慢)
    stations = Station.query.limit(10).all()
    
    # 3. 資料庫拿出來的是 Python 物件，前端看不懂，必須手動轉成 JSON 字典
    result = []
    for s in stations:
        result.append({
            'station_id': s.station_id,
            'station_name': s.station_name,
            # Decimal 和 Time 型態無法直接轉 JSON，需要轉成 float 或 string
            'latitude': float(s.latitude) if s.latitude else None,
            'longitude': float(s.longitude) if s.longitude else None,
            'arrive_time': str(s.arrive_time) if s.arrive_time else None
        })
        
    # 4. 回傳 JSON 格式給前端
    return jsonify({'status': 'success', 'data': result})
