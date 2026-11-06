import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

messages_db = []  # Respaldo en memoria si Supabase no está configurado
participants = {
    "rosa": {"label": "Rosa", "last_seen": 0, "typing_until": 0},
    "azul": {"label": "Azul", "last_seen": 0, "typing_until": 0},
}
SECRET_PASSWORD = os.environ.get("APP_PASSWORD", "0220").strip()
PRESENCE_TIMEOUT = 25
TZ = ZoneInfo(os.environ.get("APP_TZ", "America/Mexico_City"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
TABLE = os.environ.get("SUPABASE_TABLE", "messages")
USE_DB = bool(SUPABASE_URL and SUPABASE_KEY)
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def db_url():
    return f"{SUPABASE_URL}/rest/v1/{TABLE}"


def format_row(row):
    hora = ""
    try:
        dt = datetime.fromisoformat(str(row.get("created_at", "")).replace("Z", "+00:00"))
        hora = dt.astimezone(TZ).strftime("%I:%M %p")
    except Exception:
        pass
    return {"id": row["id"], "sender": row.get("sender"), "text": row.get("text"), "time": hora}


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
        hora = datetime.now(TZ).strftime("%I:%M %p")
        try:
            if USE_DB:
                r = requests.post(
                    db_url(),
                    headers={**HEADERS, "Prefer": "return=representation"},
                    json={"sender": sender, "text": text, "time": hora},  # <-- Se añadió "time": hora
                    timeout=10,
                )
                r.raise_for_status()
                new_msg = format_row(r.json()[0])
            else:
                new_msg = {
                    "id": max((m["id"] for m in messages_db), default=0) + 1,
                    "sender": sender, "text": text, "time": hora,
                }
                messages_db.append(new_msg)
        except Exception as e:
            app.logger.error("Error guardando mensaje: %s", e)
            return jsonify({"status": "error", "message": "No se pudo guardar."}), 500
        return jsonify({"status": "success", "message": new_msg})

    try:
        if USE_DB:
            r = requests.get(
                db_url(),
                headers=HEADERS,
                params={"select": "id,sender,text,created_at", "order": "created_at.asc"},
                timeout=10,
            )
            r.raise_for_status()
            return jsonify([format_row(row) for row in r.json()])
    except Exception as e:
        app.logger.error("Error leyendo mensajes: %s", e)
        return jsonify([])
    return jsonify(messages_db)


@app.route("/api/messages/delete", methods=["POST"])
def delete_message():
    global messages_db
    data = request.get_json(silent=True) or {}
    msg_id = data.get("id")
    if msg_id is None or str(msg_id).strip() == "":
        return jsonify({"status": "error", "message": "ID no válido"}), 400
    try:
        if USE_DB:
            r = requests.delete(db_url(), headers=HEADERS, params={"id": f"eq.{msg_id}"}, timeout=10)
            r.raise_for_status()
        else:
            messages_db = [m for m in messages_db if str(m["id"]) != str(msg_id)]
    except Exception as e:
        app.logger.error("Error eliminando mensaje: %s", e)
        return jsonify({"status": "error", "message": "No se pudo eliminar."}), 500
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
            "typing": active and info["typing_until"] > now,
        }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
