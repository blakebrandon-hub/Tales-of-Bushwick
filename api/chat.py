import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

BASE_PROMPT = """You are the narrator of TALES OF BUSHWICK, a text adventure about surviving New York.
TONE: Dry, observational, affectionately cynical.
CORE PRINCIPLE: Mundane situations escalate in plausible, annoying ways.

IMPORTANT: You must output ONLY valid JSON. No markdown fencing.
Structure:
{
  "text": "The narrative description of the scene...",
  "system": "A short status update (e.g. 'Status: Social Anxiety increased')",
  "choices": [
    {"text": "Option 1 action", "cost": 0, "damage": 5},
    {"text": "Option 2 action", "cost": 0, "damage": 0}
  ]
}

- Keep narrative text under 80 words.
- Provide exactly 2-4 choices.
- 'cost' is money spent. 'damage' is dignity lost.
- If the user action was successful, make the next scene slightly weird.
- If the user failed, make it socially awkward."""

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@app.route('/')
def index():
    return send_from_directory(ROOT_DIR, 'index.html')


@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        return jsonify({'status': 'ok'}), 200

    api_key = os.environ.get('GEMINI_API_KEY', None)
    if not api_key:
        return jsonify({'content': None}), 200

    body = request.get_json()
    game_state = body.get('gameState', {})
    context = body.get('context', '')
    messages = body.get('messages', [])

    if not messages:
        messages = [{'role': 'user', 'content': 'Start Game'}]

    # Convert messages to Gemini format
    gemini_messages = []
    for m in messages:
        role = 'model' if m['role'] == 'assistant' else 'user'
        gemini_messages.append({'role': role, 'parts': [{'text': m['content']}]})

    system_text = BASE_PROMPT + f"\n\nCurrent State: Dignity: {game_state.get('dignity')}, Cash: {game_state.get('liquidity')}, Time: {game_state.get('time')}. Context: {context}"

    payload = {
        'system_instruction': {'parts': [{'text': system_text}]},
        'contents': gemini_messages,
        'generationConfig': {'temperature': 0.6, 'maxOutputTokens': 1000}
    }

    resp = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent',
        headers={'x-goog-api-key': api_key, 'content-type': 'application/json'},
        json=payload,
        timeout=30
    )

    if not resp.ok:
        return jsonify({'error': resp.text}), resp.status_code

    raw = resp.json()['candidates'][0]['content']['parts'][0]['text']
    raw = raw.replace('```json', '').replace('```', '').strip()

    return jsonify({'content': raw})


if __name__ == '__main__':
    app.run(debug=True)
