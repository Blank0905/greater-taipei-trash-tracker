import pymysql
from dbutils.pooled_db import PooledDB
from config import DB_CONFIG

# 建立資料庫連線池
pool = PooledDB(
    creator=pymysql,  # 使用 PyMySQL
    maxconnections=10, # 連線池最大連線數
    mincached=2,       # 初始化時，池中至少存在的空閒連線數
    blocking=True,     # 連線池滿了後，新的請求是否要等待
    host=DB_CONFIG['host'],
    port=int(DB_CONFIG['port']),
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password'],
    database=DB_CONFIG['database'],
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor # 讓回傳結果自動變成 Python 字典格式
)

def get_db_connection():
    """從連線池中拿一個連線出來"""
    return pool.connection()
