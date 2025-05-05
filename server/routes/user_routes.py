import bcrypt
from flask import Blueprint, request, jsonify
from database import users_collection
from services.user_service import UserService
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from flask_cors import cross_origin

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/register", methods=["POST"])
@cross_origin(origins="http://localhost:5173")
def register():
    return UserService.register_user(request.json)

@user_bp.route("/login", methods=["POST"])
@cross_origin(origins="http://localhost:5173")
def login():
    return UserService.login_user(request.json)

@user_bp.route("/<login>", methods=["GET"])
def get_user(login):
    return UserService.get_user(login)


@user_bp.route("/update", methods=["PUT"])
def update_user():
    data = request.json

    if not data or "login" not in data:
        return jsonify({"error": "Логин обязателен"}), 400

    login = data.pop("login")
    update_data = {k: v for k, v in data.items() if v}

    if not update_data:
        return jsonify({"error": "Нет изменений"}), 400

    try:
        users_collection.update_one({"login": login}, {"$set": update_data})
        return jsonify({"message": "Данные обновлены"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route("/<login>", methods=["DELETE"])
def delete_current_user(login):
    return UserService.delete_user(login)

@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    verify_jwt_in_request()
    jwt_data = get_jwt()

    print("JWT данные:", jwt_data)
    print("Заголовки запроса:", request.headers)

    login = get_jwt_identity()
    print("Логин из токена:", login)

    user = users_collection.find_one({"login": login})
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    return jsonify({"login": user["login"]}), 200


@user_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Выход выполнен успешно"}), 200

@user_bp.route("/delete", methods=["DELETE"])
def delete_user():
    data = request.json

    if not data or "login" not in data:
        return jsonify({"error": "Логин обязателен"}), 400

    login = data["login"]
    return UserService.delete_user(login)

@user_bp.route("/reset_password", methods=["POST"])
def reset_password():
    data = request.json
    login = data.get("login")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not login or not new_password or not confirm_password:
        return jsonify({"error": "Все поля обязательны"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Пароли не совпадают"}), 400

    user = users_collection.find_one({"login": login})
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    users_collection.update_one({"login": login}, {"$set": {"password": hashed_password.decode("utf-8")}})

    return jsonify({"message": "Пароль успешно изменён"}), 200