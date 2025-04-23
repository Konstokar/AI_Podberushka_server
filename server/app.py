from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import subprocess, atexit

from config import SECRET_KEY

# Подключение маршрутов
from routes.user_routes import user_bp
from routes.collection_routes import collection_bp
from routes.ml_routes import ml_bp

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app, supports_credentials=True)

load_dotenv()
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_SECRET_KEY"] = SECRET_KEY
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
jwt = JWTManager(app)

app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(collection_bp, url_prefix="/api/collections")
app.register_blueprint(ml_bp, url_prefix="/api/ml")

# --- Анализ рынка: функция запуска ---
def run_market_analysis():
    print("[APScheduler] Запуск анализа рынка...")
    try:
        subprocess.run(["python", "ml/main.py"], check=True)
        print("[APScheduler] Анализ завершён")
    except subprocess.CalledProcessError as e:
        print(f"[APScheduler] Ошибка при запуске анализа рынка: {e}")

# --- Планировщик ---
scheduler = BackgroundScheduler()
scheduler.start()

# Повторяющийся запуск каждый час
scheduler.add_job(
    run_market_analysis,
    trigger=IntervalTrigger(hours=1),
    id='market_analysis_job',
    replace_existing=True
)

# Однократный запуск через 2 минуты после старта
scheduler.add_job(
    run_market_analysis,
    trigger=DateTrigger(run_date=datetime.now() + timedelta(minutes=2)),
    id='initial_market_analysis',
    replace_existing=True
)

atexit.register(lambda: scheduler.shutdown())

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)