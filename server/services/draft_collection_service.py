from models.draft_collection_model import DraftCollection
from flask import jsonify

class DraftCollectionService:
    @staticmethod
    def save_draft(login, draft_data):
        try:
            DraftCollection.save(login, draft_data)
            return jsonify({"message": "Подборка сохранена"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_draft(login):
        draft = DraftCollection.get(login)
        if draft:
            return jsonify(draft), 200
        return jsonify({"error": "Черновик не найден"}), 404

    @staticmethod
    def delete_draft(login):
        try:
            DraftCollection.delete(login)
            return jsonify({"message": "Черновик удалён"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500