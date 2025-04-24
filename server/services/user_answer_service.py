from flask import jsonify
from models.user_answer_model import UserAnswer

class UserAnswerService:
    @staticmethod
    def save_user_answers(login, answers):
        try:
            UserAnswer.save_answers(login, answers)
            return jsonify({"message": "Ответы сохранены"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def dump_answers_to_file(login, filepath="ml/user_answers.json"):
        try:
            answers = UserAnswer.get_answers(login)
            if not answers:
                return False
            import json
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(answers, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print("Ошибка при выгрузке ответов:", e)
            return False