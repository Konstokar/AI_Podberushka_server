from database import draft_collections_collection

class DraftCollection:
    @staticmethod
    def save_draft(login, data):
        draft_collections_collection.update_one(
            {"user_login": login},
            {"$set": {"data": data}},
            upsert=True
        )

    @staticmethod
    def get_draft(login):
        entry = draft_collections_collection.find_one({"user_login": login})
        return entry["data"] if entry else None

    @staticmethod
    def delete_draft(login):
        draft_collections_collection.delete_one({"user_login": login})