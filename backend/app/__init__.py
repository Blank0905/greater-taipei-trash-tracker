from flask import Flask
from flask_cors import CORS
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 允許跨來源請求 (前端 React 會用到)
    CORS(app)

    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Flask is running!'}

    # 註冊 API 路由 (Blueprint)
    from app.api.routes import bp as stations_bp
    app.register_blueprint(stations_bp)

    return app
