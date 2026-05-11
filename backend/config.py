import os

# 保留給舊的 ETL 腳本 (newimport.py) 使用
DB_CONFIG = {
    'host': 'localhost',
    'port': '3306',
    'database': 'garbage_db',
    'user': 'root',
    'password': ''
}

class Config:
    # 預設開發環境的 MySQL 連線字串 (使用 PyMySQL)
    # 格式: mysql+pymysql://<帳號>:<密碼>@<主機>:<Port>/<資料庫名稱>
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost:3306/garbage_db'
    
    # 關閉不必要的追蹤以節省記憶體
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # LINE Bot 的金鑰 (未來會用到)
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET') or 'YOUR_LINE_CHANNEL_SECRET'
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN') or 'YOUR_LINE_CHANNEL_ACCESS_TOKEN'
