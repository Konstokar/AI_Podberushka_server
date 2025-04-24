from flask import jsonify
import json
import subprocess
import time
from database import collections_collection
from models.collection_model import Collection


class CollectionService:
    @staticmethod
    def create_collection(data):
        if "user_login" not in data or not data["user_login"]:
            return {"error": "Не указан логин пользователя"}, 400

        expected_return = data.get("expected_return")
        if expected_return is None:
            return {"error": "Отсутствует доходность"}, 400

        collection_id = Collection.create_collection(data)
        return {"message": "Подборка создана", "collection_id": str(collection_id)}

    @staticmethod
    def get_collections(user_login):
        collections = list(collections_collection.find({"user_login": user_login}))

        for collection in collections:
            collection["_id"] = str(collection["_id"])
        return jsonify({"collections": collections}), 200

    @staticmethod
    def get_collection(collection_id):
        collection = Collection.get_collection_by_id(collection_id)
        if not collection:
            return {"error": "Подборка не найдена"}, 404
        return {
            "id": str(collection["_id"]),
            "name": collection["name"],
            "creation_date": collection["creation_date"],
            "goal": collection["goal"],
            "expected_return": collection["expected_return"],
            "risk_category": collection["risk_category"],
            "deadline": collection["deadline"],
            "stocks": collection["stocks"],
            "bonds": collection["bonds"]
        }

    @staticmethod
    def delete_collection(collection_id):
        deleted = Collection.delete_collection(collection_id)
        if deleted.deleted_count == 0:
            return {"error": "Подборка не найдена"}, 404
        return {"message": "Подборка удалена"}

    @staticmethod
    def get_draft_collection():
        subprocess.run(["python", "ml/main1.py"])
        time.sleep(2)

        with open("ml/selected_securities.json", "r", encoding="utf-8") as f:
            draft_collection = json.load(f)

        return draft_collection
