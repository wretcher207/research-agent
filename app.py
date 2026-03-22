# app.py
from flask import Flask, request, jsonify
from agent import run_agent

app = Flask(__name__)

sessions = {}


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "online", "agent": "research-agent"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Request body must include a 'question' field."}), 400

    question   = data["question"]
    session_id = data.get("session_id", "default")

    if session_id not in sessions:
        sessions[session_id] = []

    answer, updated_history = run_agent(question, sessions[session_id])
    sessions[session_id] = updated_history

    return jsonify({
        "answer":     answer,
        "session_id": session_id,
        "turns":      len([m for m in updated_history if m["role"] == "user"])
    })


@app.route("/clear", methods=["POST"])
def clear():
    data       = request.get_json() or {}
    session_id = data.get("session_id", "default")
    sessions.pop(session_id, None)
    return jsonify({"status": "cleared", "session_id": session_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)