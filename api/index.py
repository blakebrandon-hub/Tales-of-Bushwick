import os
from flask import Flask, send_from_directory

app = Flask(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/')
def index():
    return send_from_directory(ROOT_DIR, 'index.html')
