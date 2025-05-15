import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import jsonify
from database import users_collection, collections_collection
from config import SECRET_KEY
from models.user_model import User


class UserService:
    @staticmethod
    def register_user(data):
        print("Получены данные для регистрации:", data)

        required_fields = ["login", "email", "phone", "password", "birthdate"]
        if not all(field in data and data[field] for field in required_fields):
            print("Ошибка: не все поля заполнены")
            return jsonify({"error": "Все поля обязательны"}), 400

        if users_collection.find_one({"login": data["login"]}):
            print("Ошибка: пользователь с таким логином уже существует")
            return jsonify({"error": "Пользователь с таким логином уже существует"}), 400

        hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

        user = {
            "login": data["login"],
            "email": data["email"],
            "phone": data["phone"],
            "password": hashed_password.decode("utf-8"),
            "birthdate": data["birthdate"],
        }

        result = users_collection.insert_one(user)
        print("Добавлен новый пользователь, ID:", result.inserted_id)

        return jsonify({"message": "Пользователь зарегистрирован успешно"}), 201

    @staticmethod
    def login_user(data):
        if "login" not in data or "password" not in data:
            return jsonify({"error": "Введите логин и пароль"}), 400

        user = users_collection.find_one({"login": data["login"]})
        if not user or not bcrypt.checkpw(data["password"].encode("utf-8"), user["password"].encode("utf-8")):
            return jsonify({"error": "Неверный логин или пароль"}), 401

        token = jwt.encode(
            {"login": user["login"], "exp": datetime.utcnow() + timedelta(hours=24)},
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({"message": "Авторизация успешна", "token": token, "login": user["login"]}), 200

    @staticmethod
    def delete_user(login):
        user = users_collection.find_one({"login": login})

        if not user:
            return {"error": "Пользователь не найден"}, 404

        users_collection.delete_one({"login": login})

        collections_collection.delete_many({"user_login": login})

        return {"message": "Пользователь и его подборки удалены"}, 200

    @staticmethod
    def get_user(login):
        user = User.get_user_by_login(login)
        if user:
            user["_id"] = str(user["_id"])
            return jsonify(user), 200
        return jsonify({"error": "Пользователь не найден"}), 404