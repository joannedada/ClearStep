from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import json

app = Flask(__name__, static_folder='.', static_url_path='')

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def build_prompt(msg):
    return f"""
You are a calm, clear cognitive load reduction assistant. Analyze the message below and return ONLY a JSON object — no extra text, no markdown, no explanation.

Rules:
- risk_level: exactly one of "Safe", "Caution", or "High Risk"
- meaning: ONE sentence only. Max 12 words. Simple and calm. No technical words. No brand names.
- signals: max 3 items. Each must be 2-3 words only. Label the pattern, not the detail.
- next_steps: max 2 items. Always lead with the most protective action.
- If Safe: signals must be ["No suspicious signals"], next_steps should be short and reassuring
- Never use fear-based language. Never use jargon. Always be calm and supportive.
- Only include signals that are clearly present in the message. Do not infer.

Return ONLY this JSON:
{{
  "risk_level": "Safe | Caution | High Risk",
  "meaning": "one short sentence, max 12 words",
  "signals": ["signal 1", "signal 2", "signal 3"],
  "next_steps": ["step 1", "step 2"]
}}

Message: "{msg}"
"""

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"error": "Missing message"}), 400

    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "Missing ANTHROPIC_API_KEY"}), 500

    prompt = build_prompt(msg)

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )

    if response.status_code != 200:
        return jsonify({"error": response.text}), response.status_code

    result = response.json()
    raw_text = result["content"][0]["text"].strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_text)
        return jsonify(parsed)
    except Exception:
        return jsonify({"error": "Model returned invalid JSON", "raw": raw_text}), 500

if __name__ == "__main__":
    app.run()