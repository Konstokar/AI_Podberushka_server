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
    def generate_portfolio(market_data, login):
        try:
            input_data = json.dumps({"market_data": market_data, "user_answers": {}})
            result = subprocess.run(["python", "ml/main1.py"], input=input_data, capture_output=True, text=True)

            with open("ml/selected_securities.json", "r", encoding="utf-8") as f:
                portfolio_data = json.load(f)

            if login:
                from models.draft_collection_model import DraftCollection
                DraftCollection.save_draft(login, portfolio_data)

            return portfolio_data
        except Exception as e:
            return {"error": str(e)}, 500
