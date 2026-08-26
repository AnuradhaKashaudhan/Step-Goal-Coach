"""
app.py
------
Flask backend for the Step Goal Coach.

Routes:
    GET  /                -> serves the frontend
    POST /api/chat        -> {"message": "..."} -> runs the agent, returns
                              its reply plus the fresh dashboard state
    GET  /api/state        -> current dashboard state (today + week), no LLM
                               call — used for the initial page load / polling
    POST /api/goal          -> {"goal": 10000} -> updates the daily step goal
"""

from flask import Flask, request, jsonify, render_template

from storage import get_full_state, set_goal
from agent import run_agent

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(get_full_state())


@app.route("/api/goal", methods=["POST"])
def api_goal():
    body = request.get_json(force=True) or {}
    goal = body.get("goal")
    if not isinstance(goal, (int, float)) or goal <= 0:
        return jsonify({"error": "goal must be a positive number"}), 400
    progress = set_goal(int(goal))
    return jsonify({"progress": progress})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    body = request.get_json(force=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        reply = run_agent(message)
    except RuntimeError as e:
        # Most commonly: missing GEMINI_API_KEY
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Agent error: {e}"}), 500

    return jsonify({"reply": reply, "state": get_full_state()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
