from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash
from app.db import get_db_connection
from config import Config
import pymysql

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/register', methods=['GET'])
def show_register_page():
    # 渲染 HTML 並把 config.py 的 LIFF_ID 塞進去
    return render_template('register.html', liff_id=Config.LINE_LIFF_ID)

@bp.route('/register', methods=['POST'])
def register_user():
    """
    接收前端 (或 LINE LIFF 網頁) 傳來的註冊資料，寫入資料庫
    預期收到的 JSON 格式:
    {
        "username": "testuser",
        "email": "test@example.com",  # 可選填
        "password": "mypassword"
    }
    """
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'status': 'error', 'message': '必須提供 username 與 password'}), 400

    username = data.get('username')
    email = data.get('email')
    raw_password = data.get('password')
    line_user_id = data.get('line_user_id') # 從 LIFF 拿到的重要 ID

    hashed_password = generate_password_hash(raw_password)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 檢查是否重複註冊 (包含 LINE ID 檢查)
            check_sql = "SELECT user_id FROM users WHERE username = %s OR (email = %s AND email IS NOT NULL) OR line_user_id = %s"
            cursor.execute(check_sql, (username, email, line_user_id))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': '此帳號、Email 或 LINE 已經被綁定過'}), 409

            # 寫入資料庫
            insert_sql = """
                INSERT INTO users (line_user_id, username, email, password_hash, role)
                VALUES (%s, %s, %s, %s, 'user')
            """
            cursor.execute(insert_sql, (line_user_id, username, email, hashed_password))
            
            conn.commit()
            new_user_id = cursor.lastrowid

            return jsonify({
                'status': 'success', 
                'message': '註冊成功！',
                'data': {
                    'user_id': new_user_id,
                    'username': username
                }
            }), 201

    except Exception as e:
        conn.rollback() # 發生錯誤就退回，保護資料庫
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()