# coding=utf-8
import uuid
from pymongo import MongoClient

class User:
    def __init__(self, username):
        self.username = username
        self.user_id = str(uuid.uuid4())  # 生成唯一的 user_id

    @staticmethod
    def create_user(username):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps
        users_collection = db.users

        # 检查是否已经有该用户名的用户
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return existing_user['user_id']

        # 创建新用户
        new_user = User(username)
        users_collection.insert_one({
            "username": new_user.username,
            "user_id": new_user.user_id
        })
        return new_user.user_id
