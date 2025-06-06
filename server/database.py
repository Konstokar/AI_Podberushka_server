from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "investment_app")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db["users"]
collections_collection = db["collections"]
user_answers_collection = db["user_answers"]
risk_assessment_collection = db["risk_assessment"]
draft_collections_collection = db["draft_collections"]