from datetime import datetime

from database import collections_collection
from bson import ObjectId

class Collection:
    @staticmethod
    def create_collection(data):
        collection = {
            "user_login": data.get("user_login"),
            "name": data["name"],
            "creation_date": data.get("creation_date", datetime.utcnow()),
            "goal": data["goal"],
            "expected_return": data.get("expected_return"),
            "risk_category": data.get("risk_category"),
            "deadline": data.get("deadline"),
            "stocks": data["stocks"],
            "bonds": data["bonds"]
        }
        return collections_collection.insert_one(collection).inserted_id

    @staticmethod
    def get_collections_by_user(user_login):
        return list(collections_collection.find({"user_login": user_login}))

    @staticmethod
    def get_collection_by_id(collection_id):
        return collections_collection.find_one({"_id": ObjectId(collection_id)})

    @staticmethod
    def delete_collection(collection_id):
        return collections_collection.delete_one({"_id": ObjectId(collection_id)})