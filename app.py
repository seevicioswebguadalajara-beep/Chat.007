import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# Configuración de Supabase desde las variables de entorno de Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/messages", methods=["GET"])
def get_messages():
    try:
        response = supabase.table("messages").select("*").order("created_at", desc=False).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/messages", methods=["POST"])
def post_message():
    data = request.get_json()
    message_text = data.get("text")
    sender = data.get("sender", "Anónimo")
    
    if not message_text:
        return jsonify({"error": "El mensaje no puede estar vacío"}), 400

    try:
        response = supabase.table("messages").insert({
            "text": message_text,
            "sender": sender
        }).execute()
        return jsonify(response.data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
