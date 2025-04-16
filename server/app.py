from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import SECRET_KEY

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app, supports_credentials=True)

load_dotenv()
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_SECRET_KEY"] = SECRET_KEY
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
jwt = JWTManager(app)

print("Сгенерирован новый SECRET_KEY:", SECRET_KEY)

from routes.user_routes import user_bp
from routes.collection_routes import collection_bp
from routes.ml_routes import ml_bp

app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(collection_bp, url_prefix="/api/collections")
app.register_blueprint(ml_bp, url_prefix="/api/ml")

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)