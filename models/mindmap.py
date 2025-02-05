# coding=utf-8
from pymongo import MongoClient
from datetime import datetime, timezone

class Mindmap:
    @staticmethod
    def get_by_uid(uid):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps
        mindmap_collection = db.mindmap_collection

        # 查找匹配 UID 的思维导图
        mindmap_data = mindmap_collection.find_one({"root.data.uid": uid}, {"_id": 0})  # 不返回 MongoDB 的 _id 字段

        return mindmap_data
    
    @staticmethod
    def save_mindmap(user_id, pdf_filename, level_of_detail, mindmap_data):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps  # 连接到 mindmaps 数据库
        mindmap_collection = db.system_data  # 连接到新的集合 mindmap_data
        print('connected')
        current_time = datetime.now(timezone.utc)

        # 创建一个记录包含用户信息、文件名、思维导图数据等
        record = {
            "user_id": user_id,
            "pdf_filename": pdf_filename,
            "level_of_detail": level_of_detail,
            "mindmap_data": mindmap_data,
            "created_at": current_time
        }

        # 插入到数据库中
        mindmap_collection.insert_one(record)
        return record
    
    @staticmethod
    def update_mindmap(mindmap_data):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps
        mindmap_collection = db.mindmap_collection

        # 查找并更新思维导图数据，假设每个思维导图有唯一的 root.uid 作为标识
        result = mindmap_collection.update_one(
            {"root.data.uid": mindmap_data['root']['data']['uid']},
            {"$set": mindmap_data},
            upsert=True  # 如果记录不存在，创建新记录（插入一个新的思维导图document）
        )

        # 如果匹配到至少一条记录，返回True
        return result.modified_count > 0 or result.upserted_id is not None

#是否包含了两种情况：保存全新的思维导图，更新思维导图的某一部分的数据？  --检查