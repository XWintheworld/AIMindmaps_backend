# coding=utf-8
from pymongo import MongoClient

#初始化与 MongoDB 的连接。此代码在项目启动时由 app.py 调用
def initialize_db(app):
    app.config['MONGO_CLIENT'] = MongoClient(app.config['MONGO_URI'])
    return app.config['MONGO_CLIENT']
