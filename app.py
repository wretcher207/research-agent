# app.py
from flask import Flask, request, jsonify
from agent import run_agent
from supabase_sessions import get_session, save_session

app = Flask(__name__, static_folder=".", static_url_path="")


@app.route("/", methods=["GET"])
def index():
    return app.send_static_file("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Request body must include a 'question' field."}), 400

    question   = data["question"]
    session_id = data.get("session_id", "default")

    history = get_session(session_id)
    answer, updated_history = run_agent(question, history)
    save_session(session_id, updated_history)

    return jsonify({
        "answer":     answer,
        "session_id": session_id,
        "turns":      len([m for m in updated_history if m["role"] == "user"])
    })


@app.route("/clear", methods=["POST"])
def clear():
    data       = request.get_json() or {}
    session_id = data.get("session_id", "default")
    save_session(session_id, [])
    return jsonify({"status": "cleared", "session_id": session_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)