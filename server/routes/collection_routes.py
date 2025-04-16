from flask import Blueprint, request
from services.collection_service import CollectionService

collection_bp = Blueprint("collection_bp", __name__)

@collection_bp.route("/", methods=["POST"])
def create_collection():
    data = request.json
    return CollectionService.create_collection(data)

@collection_bp.route("/user/<user_login>", methods=["GET"])
def get_collections(user_login):
    return CollectionService.get_collections(user_login)

@collection_bp.route("/<collection_id>", methods=["GET"])
def get_collection(collection_id):
    return CollectionService.get_collection(collection_id)

@collection_bp.route("/<collection_id>", methods=["DELETE"])
def delete_collection(collection_id):
    return CollectionService.delete_collection(collection_id)

@collection_bp.route("/draft", methods=["GET"])
def get_draft_collection():
    return CollectionService.get_draft_collection()

@collection_bp.route("/save", methods=["POST"])
def save_collection():
    data = request.json
    return CollectionService.create_collection(data)