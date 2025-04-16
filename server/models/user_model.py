from database import users_collection
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    @staticmethod
    def create_user(data):
        hashed_password = generate_password_hash(data["password"])
        user = {
            "login": data["login"],
            "email": data["email"],
            "phone": data["phone"],
            "password": hashed_password,
            "birthdate": data["birthdate"]
        }
        return users_collection.insert_one(user).inserted_id

    @staticmethod
    def get_user_by_login(login):
        return users_collection.find_one({"login": login})

    @staticmethod
    def update_user(login, updated_data):
        update_query = {k: v for k, v in updated_data.items() if v}
        if "password" in update_query:
            update_query["password"] = generate_password_hash(update_query["password"])
        return users_collection.update_one({"login": login}, {"$set": update_query})

    @staticmethod
    def delete_user(login):
        from database import collections_collection
        collections_collection.delete_many({"user_login": login})
        return users_collection.delete_one({"login": login})