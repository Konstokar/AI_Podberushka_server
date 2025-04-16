import os
import json
from flask import Blueprint, request, jsonify, session

from services.ml_service import MLService

ml_bp = Blueprint("ml_bp", __name__)
USER_ANSWERS_PATH = os.path.join("ml", "user_answers.json")

FILES_TO_CLEAR = [
    "ml/user_answers.json",
    "ml/risk_assessment.json",
    "ml/selected_securities.json"
]


@ml_bp.route("/analyze_market", methods=["GET"])
def analyze_market():
    return jsonify(MLService.analyze_market())


@ml_bp.route("/generate_portfolio", methods=["POST"])
def generate_portfolio():
    data = request.json
    market_data = data.get("market_data")
    user_answers = data.get("user_answers")

    if not market_data or not user_answers:
        return jsonify({"error": "Отсутствуют входные данные"}), 400

    return jsonify(MLService.generate_portfolio(market_data, user_answers))


@ml_bp.route("/save_answers", methods=["POST"])
def save_answers():
    try:
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"error": "Неверный формат данных"}), 400

        os.makedirs(os.path.dirname(USER_ANSWERS_PATH), exist_ok=True)

        with open(USER_ANSWERS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return jsonify({"message": "Ответы сохранены"}), 200
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