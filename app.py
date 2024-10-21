# coding=utf-8
from flask import Flask
from routes.mindmap_routes import mindmap_bp
from utils.db import initialize_db
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')

# 注册蓝图
app.register_blueprint(mindmap_bp, url_prefix='/api/mindmap')

# 初始化MongoDB
initialize_db(app)

# 允许所有来源的跨域请求
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)
