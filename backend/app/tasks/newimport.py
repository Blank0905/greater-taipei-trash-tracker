# importer.py
import pandas as pd
import mysql.connector
from mysql.connector import Error
import re
import numpy as np
import math
import sys
import os

# 讓腳本能往上找到 backend/ 目錄裡的 config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config import DB_CONFIG

# 設定工作目錄為腳本所在目錄
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
print(f"[工作目錄] {os.getcwd()}")

class GarbageTruckImporter:
    
    def __init__(self, host='localhost', port = 3306, database='test_garbage', user='root', password=''):
        print(f"[連接中...] 連接到 {host}:{port} database={database}")
        sys.stdout.flush()
        
        try:
            self.conn = mysql.connector.connect(
                host=host,
                port = port,
                database=database,
                user=user,
                password=password,
                charset='utf8mb4',
                connection_timeout=60,
                read_timeout=600,
                write_timeout=600,
                autocommit=False
            )
            print(f"[✓ 連接成功]")
            sys.stdout.flush()
        except Error as e:
            print(f"[✗ 連接失敗] {e}")
            sys.stdout.flush()
            raise
            
        self.cursor = self.conn.cursor()
        self.batch_count = 0
        self.batch_size = 100
        self.query_count = 0
    
    # ========== 站點名稱清理 ==========
    def _clean_station_name(self, name: str, city: str, district: str) -> str:
        if not name:
            return name
        
        name = str(name).strip()
        prefixes_to_remove = []
        
        if city and district:
            prefixes_to_remove.append(f"{city}{district}")
            if '台' in city:
                prefixes_to_remove.append(f"{city.replace('台', '臺')}{district}")
            if '臺' in city:
                prefixes_to_remove.append(f"{city.replace('臺', '台')}{district}")
        
        if city:
            prefixes_to_remove.append(city)
            if '台' in city:
                prefixes_to_remove.append(city.replace('台', '臺'))
            if '臺' in city:
                prefixes_to_remove.append(city.replace('臺', '台'))
        
        if district:
            prefixes_to_remove.append(district)
        
        prefixes_to_remove.sort(key=len, reverse=True)
        
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                break
        
        return name
    
    # ========== areas 表管理 ==========
    def _get_or_create_area(self, city: str, district: str = None, village: str = None) -> int:
        """
        取得或建立一筆 areas 記錄，依 (city, district, village) 唯一鍵。
        village=None 代表區層級（用於 routes）。
        village 有值代表里層級（用於 stations）。
        """
        city    = self._clean(city)
        district = self._clean(district)
        village  = self._clean(village)

        # 先查是否已存在
        sql_select = """
            SELECT areas_id FROM areas
            WHERE city = %s
              AND (district <=> %s)
              AND (village  <=> %s)
        """
        self.cursor.execute(sql_select, (city, district, village))
        row = self.cursor.fetchone()
        if row:
            return row[0]

        # 不存在則新增
        sql_insert = """
            INSERT INTO areas (city, district, village)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(sql_insert, (city, district, village))
        return self.cursor.lastrowid

    # ========== 台北市 ==========
    def import_taipei(self, csv_path: str):
        print(f"\n[台北市] 開始匯入 {csv_path}")
        sys.stdout.flush()
        
        df = pd.read_csv(csv_path, dtype=str)
        df = df.replace({np.nan: None})
        print(f"[台北市] 讀取 {len(df)} 筆記錄")
        sys.stdout.flush()
        
        route_groups = df.groupby(['局編', '車次', '路線', '分隊', '車號', '行政區'])
        total_routes = len(route_groups)
        print(f"[台北市] 分組為 {total_routes} 條路線")
        sys.stdout.flush()
        
        route_idx = 0
        for (route_code, trip, route_name, team, car_num, district), group in route_groups:
            route_idx += 1
            print(f"[台北市 {route_idx}/{total_routes}] 路線: {route_name} ({len(group)} 站點)", end='\r')
            sys.stdout.flush()
            # routes → 區層級（village=None）
            route_area_id = self._get_or_create_area('台北市', district, None)
            route_id = self._insert_route(
                areas_id=route_area_id,
                route_code=route_code,
                route_name=route_name,
                car_number=car_num,
                team=team,
                trip_number=trip
            )
            
            for idx, row in group.iterrows():
                raw_name  = row['地點']
                clean_name = self._clean_station_name(raw_name, '台北市', row['行政區'])
                
                # stations → 里層級（village 有值）
                station_area_id = self._get_or_create_area('台北市', row['行政區'], row['里別'])
                station_id = self._insert_station(
                    route_id=route_id,
                    areas_id=station_area_id,
                    station_name=clean_name,
                    longitude=self._safe_float(row['經度']),
                    latitude=self._safe_float(row['緯度']),
                    arrive_time=self._parse_time_4digit(row['抵達時間']),
                    leave_time=self._parse_time_4digit(row['離開時間'])
                )
                
                self._insert_taipei_schedule(station_id)
                
                self.batch_count += 1
                if self.batch_count % self.batch_size == 0:
                    self.conn.commit()
                    print(f"  [✓ 已提交 {self.batch_count} 筆操作]", end='\r')
                    sys.stdout.flush()
        
        self.conn.commit()
        print(f"\n[台北市] ✓ 匯入完成 (共 {self.batch_count} 筆操作)")
    
    def _insert_taipei_schedule(self, station_id: int):
        for day in [2, 4, 6]:
            self._insert_schedule(station_id, day, True, True, True)
        for day in [1, 3, 5]:
            self._insert_schedule(station_id, day, True, False, False)
    
    # ========== 新北市 ==========
    def import_new_taipei(self, csv_path: str):
        print(f"\n[新北市] 開始匯入 {csv_path}")
        sys.stdout.flush()
        
        df = pd.read_csv(csv_path, dtype=str)
        df = df.replace({np.nan: None})
        print(f"[新北市] 讀取 {len(df)} 筆記錄")
        sys.stdout.flush()
        
        route_groups = df.groupby(['lineid', 'linename', 'city'])
        total_routes = len(route_groups)
        print(f"[新北市] 分組為 {total_routes} 條路線")
        sys.stdout.flush()
        
        route_idx = 0
        batch_start = self.batch_count
        
        for (line_id, line_name, district), group in route_groups:
            route_idx += 1
            print(f"[新北市 {route_idx}/{total_routes}] 路線: {line_name} ({len(group)} 站點)", end='\r')
            sys.stdout.flush()
            route_area_id = self._get_or_create_area('新北市', district, None)
            route_id = self._insert_route(
                areas_id=route_area_id,
                route_code=line_id,
                route_name=line_name
            )
            
            for idx, row in group.iterrows():
                raw_name   = row['name']
                clean_name = self._clean_station_name(raw_name, '新北市', row['city'])
                
                station_area_id = self._get_or_create_area('新北市', row['city'], row.get('village'))
                station_id = self._insert_station(
                    route_id=route_id,
                    areas_id=station_area_id,
                    station_name=clean_name,
                    sequence_order=self._safe_int(row['rank']),
                    longitude=self._safe_float(row['longitude']),
                    latitude=self._safe_float(row['latitude']),
                    arrive_time=self._parse_time_hhmm(row['time']),
                    memo=row.get('memo', '')
                )
                
                self._insert_new_taipei_schedule(station_id, row)
                
                self.batch_count += 1
                if self.batch_count % self.batch_size == 0:
                    self.conn.commit()
        
        self.conn.commit()
        print(f"\n[新北市] ✓ 匯入完成 (新增 {self.batch_count - batch_start} 筆操作)")
    
    def _insert_new_taipei_schedule(self, station_id: int, row):
        days = ['sunday', 'monday', 'tuesday', 'wednesday', 
                'thursday', 'friday', 'saturday']
        
        for day_idx, day_name in enumerate(days):
            garbage   = row.get(f'garbage{day_name}',   '') == 'Y'
            recycling = row.get(f'recycling{day_name}', '') == 'Y'
            foodscraps = row.get(f'foodscraps{day_name}', '') == 'Y'
            
            if garbage or recycling or foodscraps:
                self._insert_schedule(station_id, day_idx, garbage, recycling, foodscraps)
    
    # ========== 基隆市 ==========
    def import_keelung(self, csv_path: str):
        print(f"\n[基隆市] 開始匯入 {csv_path}")
        sys.stdout.flush()
        
        df = pd.read_csv(csv_path, dtype=str)
        df = df.replace({np.nan: None})
        print(f"[基隆市] 讀取 {len(df)} 筆記錄")
        sys.stdout.flush()
        
        route_groups = df.groupby(['編號', '清運路線名稱', '班別'])
        total_routes = len(route_groups)
        print(f"[基隆市] 分組為 {total_routes} 條路線")
        sys.stdout.flush()
        
        route_idx = 0
        batch_start = self.batch_count
        
        for (route_code, route_name, team), group in route_groups:
            route_idx += 1
            print(f"[基隆市 {route_idx}/{total_routes}] 路線: {route_name} ({len(group)} 站點)", end='\r')
            sys.stdout.flush()
            district = self._extract_keelung_district(route_name)
            
            route_area_id = self._get_or_create_area('基隆市', district, None)
            route_id = self._insert_route(
                areas_id=route_area_id,
                route_code=route_code,
                route_name=route_name,
                trip_number=team
            )
            
            for idx, row in group.iterrows():
                raw_name   = row['清運點']
                clean_name = self._clean_station_name(raw_name, '基隆市', district)
                
                # 基隆來源無里別欄位 → village=None，同樣落在區層級
                station_area_id = self._get_or_create_area('基隆市', district, None)
                station_id = self._insert_station(
                    route_id=route_id,
                    areas_id=station_area_id,
                    station_name=clean_name,
                    sequence_order=self._safe_int(row['順序']),
                    longitude=self._safe_float(row['經度']),
                    latitude=self._safe_float(row['緯度']),
                    arrive_time=self._parse_time_hhmm(row['預估到達時間']),
                    leave_time=self._parse_time_hhmm(row['預估離開時間']),
                    stay_type=row.get('停留時間', ''),
                    raw_source_id=row.get('stopId', '')
                )
                
                self._insert_keelung_schedule(station_id, row.get('回收日(星期幾)', ''))
                
                self.batch_count += 1
                if self.batch_count % self.batch_size == 0:
                    self.conn.commit()
        
        self.conn.commit()
        print(f"\n[基隆市] ✓ 匯入完成 (新增 {self.batch_count - batch_start} 筆操作)")
    
    def _extract_keelung_district(self, route_name: str) -> str:
        match = re.search(r'(暖暖區|中正區|信義區|仁愛區|中山區|安樂區|七堵區)', route_name)
        return match.group(1) if match else '基隆市'
    
    def _insert_keelung_schedule(self, station_id: int, recycle_days_str: str):
        if pd.isna(recycle_days_str) or recycle_days_str is None:
            return
        
        recycle_days_str = str(recycle_days_str).strip()
        if not recycle_days_str or recycle_days_str.lower() == 'nan':
            return
        
        day_mapping = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '日': 0, '0': 0}
        
        for day_str in recycle_days_str.split(','):
            day_str = day_str.strip()
            if day_str in day_mapping:
                self._insert_schedule(station_id, day_mapping[day_str], True, True, True)
    
    # ========== 共用方法 ==========
    def _clean(self, val):
        if val is None:
            return None
        if isinstance(val, float) and math.isnan(val):
            return None
        if str(val).strip().lower() == 'nan':
            return None
        return val

    def _insert_route(self, areas_id, route_code=None, route_name=None,
                      car_number=None, team=None, trip_number=None) -> int:
        sql = """
            INSERT INTO routes (areas_id, route_code, route_name, car_number, team, trip_number)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            self._clean(areas_id), self._clean(route_code), self._clean(route_name),
            self._clean(car_number), self._clean(team), self._clean(trip_number)
        )
        self.cursor.execute(sql, params)
        return self.cursor.lastrowid
    
    def _insert_station(self, route_id, areas_id, station_name=None,
                        sequence_order=None, longitude=None, latitude=None,
                        arrive_time=None, leave_time=None,
                        stay_type=None, memo=None, raw_source_id=None) -> int:
        sql = """
            INSERT INTO stations 
            (route_id, areas_id, station_name, sequence_order,
             longitude, latitude, arrive_time, leave_time, stay_type, memo, raw_source_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self._clean(route_id), self._clean(areas_id), self._clean(station_name),
            self._clean(sequence_order), self._clean(longitude), self._clean(latitude),
            self._clean(arrive_time), self._clean(leave_time),
            self._clean(stay_type), self._clean(memo), self._clean(raw_source_id)
        )
        self.cursor.execute(sql, params)
        return self.cursor.lastrowid
    
    def _insert_schedule(self, station_id: int, day: int, 
                         garbage: bool, recycling: bool, foodscraps: bool):
        sql = """
            INSERT INTO station_schedules 
            (station_id, day_of_week, collects_garbage, collects_recycling, collects_foodscraps)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                collects_garbage   = VALUES(collects_garbage),
                collects_recycling = VALUES(collects_recycling),
                collects_foodscraps = VALUES(collects_foodscraps)
        """
        self.cursor.execute(sql, (station_id, day, garbage, recycling, foodscraps))
    
    def _parse_time_4digit(self, t) -> str:
        if pd.isna(t) or not t:
            return None
        t = str(t).strip()
        if len(t) == 4 and t.isdigit():
            return f"{t[:2]}:{t[2:]}:00"
        if len(t) == 3 and t.isdigit():
            return f"0{t[0]}:{t[1:]}:00"
        return None
    
    def _parse_time_hhmm(self, t) -> str:
        if pd.isna(t) or not t:
            return None
        t = str(t).strip()
        if ':' in t:
            parts = t.split(':')
            if len(parts) >= 2:
                return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
        return None
    
    def _safe_float(self, val):
        try:
            if pd.isna(val) or val == '' or str(val).strip().lower() == 'nan':
                return None
            res = float(val)
            return None if math.isnan(res) else res
        except:
            return None

    def _safe_int(self, val):
        try:
            if pd.isna(val) or val == '' or str(val).strip().lower() == 'nan':
                return None
            return int(float(val))
        except:
            return None
    
    def close(self):
        self.cursor.close()
        self.conn.close()


# ========== 使用範例 ==========
if __name__ == '__main__':
    print("="*60)
    print("垃圾車資料匯入系統 - 開始")
    print("="*60)
    sys.stdout.flush()
    
    try:
        importer = GarbageTruckImporter(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        print("\n開始匯入各市資料...\n")
        sys.stdout.flush()
        
        importer.import_taipei('台北市垃圾車清運點位資訊.csv')
        importer.import_new_taipei('新北市垃圾車路線.csv')
        importer.import_keelung('route_klepb.csv')
        
        print("\n" + "="*60)
        print("✓ 全部匯入完成！")
        print("="*60)
        sys.stdout.flush()
        
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    finally:
        try:
            importer.close()
        except:
            pass
