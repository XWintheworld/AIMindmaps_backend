# coding=utf-8
from pymongo import MongoClient
from datetime import datetime, timezone

class NodeImages:
    @staticmethod
    def get_images_by_node_id(node_uid):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps
        # 查询节点的图片信息
        node_images = db.images_collection.find_one({"node_uid": node_uid}, {"_id": 0, "current_image": 1, "history_images": 1})
        return node_images
    
    @staticmethod
    def update_images_by_node_id(node_uid, new_image_url, new_prompt, history_images, user_id):
        print('loading')
        client = MongoClient('mongodb://localhost:27017/')
        print('client connnecting')
        db = client.mindmaps
        print('db connecting')
        
        # 获取当前时间， UTC timezone
        current_time = datetime.now(timezone.utc)

        print('checking time:', current_time)

        # 将新的图片和 prompt 作为当前图片保存
        current_image = {
            "url": new_image_url,
            "prompt": new_prompt
        }

        # 查找当前节点图片信息，检查是否已有记录
        existing_record = db.images_collection.find_one({"node_uid": node_uid})

        # 如果记录不存在，则设置 created_time
        if existing_record is None:
            created_time = current_time
        else:
            created_time = existing_record.get("created_time", current_time)  # 如果已有记录但没有 created_time，则设为当前时间

        # 更新或插入图片和历史图片，同时更新 last_updated 和 created_time
        result = db.images_collection.update_one(
            {"node_uid": node_uid},
            {
                "$set": {
                    "current_image": current_image,
                    "history_images": history_images,
                    "last_updated": current_time,  # 每次更新时都更新 last_updated
                    "user_id": user_id  # 保存用户ID
                },
                "$setOnInsert": {
                    "created_time": created_time  # 只在首次插入时设置 created_time
                }
            },
            upsert=True  # 如果不存在该记录则创建新的
        )

        return result.modified_count > 0 or result.upserted_id is not None

    # @staticmethod
    # def get_images_by_node_id(node_uid):
    #     client = MongoClient('mongodb://localhost:27017/')
    #     db = client.mindmaps
    #     return db.images_collection.find_one({"node_uid": node_uid})
    
    # @staticmethod
    # def update_images_by_node_id(node_uid, new_image_url, history_images):
    #     client = MongoClient('mongodb://localhost:27017/')
    #     db = client.mindmaps

    #     result = db.images_collection.update_one(
    #         {"node_uid": node_uid},
    #         {
    #             "$set": {
    #                 "current_image": new_image_url,
    #                 "history_images": history_images
    #             }
    #         },
    #         upsert=True  # 如果不存在该记录则创建新的
    #     )
    #     return result.modified_count > 0 or result.upserted_id is not None
