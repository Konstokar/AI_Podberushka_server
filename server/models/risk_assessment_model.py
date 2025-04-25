from database import risk_assessment_collection

class RiskAssessment:
    @staticmethod
    def save(data):
        risk_assessment_collection.delete_many({})
        risk_assessment_collection.insert_one({"data": data})

    @staticmethod
    def get():
        entry = risk_assessment_collection.find_one()
        return entry["data"] if entry else None