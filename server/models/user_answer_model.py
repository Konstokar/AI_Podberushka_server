from database import user_answers_collection

class UserAnswer:
    @staticmethod
    def save_answers(login, answers):
        user_answers_collection.update_one(
            {"user_login": login},
            {"$set": {"answers": answers}},
            upsert=True
        )

    @staticmethod
    def get_answers(login):
        entry = user_answers_collection.find_one({"user_login": login})
        return entry["answers"] if entry else None