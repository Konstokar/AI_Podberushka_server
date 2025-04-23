import subprocess
import json

class MLService:
    @staticmethod
    def analyze_market():
        try:
            with open("ml/risk_assessment.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def generate_portfolio(market_data, user_answers):
        try:
            input_data = json.dumps({"market_data": market_data, "user_answers": user_answers})
            result = subprocess.run(["python", "ml/main1.py"], input=input_data, capture_output=True, text=True)
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e)}, 500
