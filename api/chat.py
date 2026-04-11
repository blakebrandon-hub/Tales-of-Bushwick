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

    api_key = os.environ.get('ANTHROPIC_API_KEY', None)
    if not api_key:
        return jsonify({'content': None}), 200

    body = request.get_json()
    game_state = body.get('gameState', {})
    context = body.get('context', '')
    messages = body.get('messages', [])

    if not messages:
        messages = [{'role': 'user', 'content': 'Start Game'}]

    payload = {
        'model': 'claude-sonnet-4-6',
        'max_tokens': 1000,
        'temperature': 0.6,
        'system': [
            {
                'type': 'text',
                'text': BASE_PROMPT,
                'cache_control': {'type': 'ephemeral'}
            },
            {
                'type': 'text',
                'text': f"Current State: Dignity: {game_state.get('dignity')}, Cash: {game_state.get('liquidity')}, Time: {game_state.get('time')}. Context: {context}"
            }
        ],
        'messages': messages
    }

    resp = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'anthropic-beta': 'prompt-caching-2024-07-31'
        },
        json=payload,
        timeout=30
    )

    if not resp.ok:
        return jsonify({'error': resp.text}), resp.status_code

    raw = resp.json()['content'][0]['text']
    raw = raw.replace('```json', '').replace('```', '').strip()

    return jsonify({'content': raw})


if __name__ == '__main__':
    app.run(debug=True)
