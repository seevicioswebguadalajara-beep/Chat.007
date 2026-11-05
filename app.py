from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import time

app = Flask(__name__)

# Chat ligero para dos participantes. Los datos permanecen en memoria mientras
# el proceso está activo, igual que en la versión original.
messages_db = []
participants = {
    "rosa": {"label": "Rosa", "last_seen": 0, "typing_until": 0},
    "azul": {"label": "Azul", "last_seen": 0, "typing_until": 0},
}
SECRET_PASSWORD = "1234"  # Cambia esta clave antes de publicar el sitio.
PRESENCE_TIMEOUT = 25


def valid_color(value):
    return value if value in participants else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    color = valid_color(data.get("color"))
    password = data.get("password", "")
    if password == SECRET_PASSWORD and color:
        return jsonify({"status": "success", "user": color, "label": participants[color]["label"]})
    return jsonify({"status": "error", "message": "Selecciona un color e introduce la contraseña correcta."}), 401


@app.route("/api/messages", methods=["GET", "POST"])
def handle_messages():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        sender = valid_color(data.get("sender"))
        text = str(data.get("text", "")).strip()
        if not sender or not text:
            return jsonify({"status": "error", "message": "Mensaje no válido."}), 400
        new_msg = {
            "id": max((m["id"] for m in messages_db), default=0) + 1,
            "sender": sender,
            "text": text,
            "time": datetime.now().strftime("%I:%M %p")
        }
        messages_db.append(new_msg)
        return jsonify({"status": "success", "message": new_msg})
    return jsonify(messages_db)


@app.route("/api/messages/delete", methods=["POST"])
def delete_message():
    global messages_db
    data = request.get_json(silent=True) or {}
    try:
        msg_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "ID no válido"}), 400
    messages_db = [m for m in messages_db if m["id"] != msg_id]
    return jsonify({"status": "success"})


@app.route("/api/presence", methods=["POST"])
def update_presence():
    data = request.get_json(silent=True) or {}
    color = valid_color(data.get("user"))
    if not color:
        return jsonify({"status": "error"}), 400
    participants[color]["last_seen"] = time.time()
    participants[color]["typing_until"] = time.time() + 4 if data.get("is_typing") else 0
    return jsonify({"status": "ok"})


@app.route("/api/status")
def get_status():
    now = time.time()
    result = {}
    for color, info in participants.items():
        active = now - info["last_seen"] < PRESENCE_TIMEOUT
        result[color] = {
            "label": info["label"],
            "active": active,
            "typing": active and info["typing_until"] > now
        }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
