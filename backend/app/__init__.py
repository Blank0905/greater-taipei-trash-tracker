from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# 初始化全域的資料庫實例
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 綁定資料庫到這個 Flask App
    db.init_app(app)

    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Flask is running!'}

    # 註冊 API 路由 (Blueprint)
    from app.api.routes import bp as stations_bp
    app.register_blueprint(stations_bp)

    return app
