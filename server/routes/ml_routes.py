import os
import json
from flask import Blueprint, request, jsonify

from services.ml_service import MLService
from services.user_answer_service import UserAnswerService

ml_bp = Blueprint("ml_bp", __name__)
USER_ANSWERS_PATH = os.path.join("ml", "user_answers.json")

FILES_TO_CLEAR = [
    "ml/user_answers.json",
    "ml/selected_securities.json"
]


@ml_bp.route("/analyze_market", methods=["GET"])
def analyze_market():
    return jsonify(MLService.analyze_market())


@ml_bp.route("/generate_portfolio", methods=["POST"])
def generate_portfolio():
    try:
        login = request.json.get("login")
        if not UserAnswerService.dump_answers_to_file(login):
            return jsonify({"error": "Ответы не найдены"}), 400

        market_data = request.json.get("market_data")
        if not market_data:
            return jsonify({"error": "Отсутствуют данные рынка"}), 400

        portfolio_data = MLService.generate_portfolio(market_data, login)

        return jsonify(portfolio_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/save_answers", methods=["POST"])
def save_answers():
    try:
        data = request.json
        login = data.get("login")
        answers = data.get("answers")

        if not login or not isinstance(answers, dict):
            return jsonify({"error": "Неверный формат данных"}), 400

        return UserAnswerService.save_user_answers(login, answers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/reset", methods=["POST"])
def reset_generation():
    try:
        for file_path in FILES_TO_CLEAR:
            if os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)

        return jsonify({"message": "Файлы очищены"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500