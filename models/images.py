from pymongo import MongoClient

class NodeImages:
    @staticmethod
    def get_images_by_node_id(node_uid):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps_images
        return db.images_collection.find_one({"node_uid": node_uid})
    
    @staticmethod
    def update_images_by_node_id(node_uid, new_image_url, history_images):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.mindmaps_images
        result = db.images_collection.update_one(
            {"node_uid": node_uid},
            {
                "$set": {
                    "current_image": new_image_url,
                    "history_images": history_images
                }
            },
            upsert=True  # 如果不存在该记录则创建新的
        )
        return result.modified_count > 0 or result.upserted_id is not None
