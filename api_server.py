import os
import json
from flask import Flask, jsonify

app = Flask(__name__)

# Load Stores.json located in the same repo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORES_PATH = os.path.join(BASE_DIR, "Stores.json")

with open(STORES_PATH, "r") as f:
    STORES = json.load(f)

@app.get("/")
def home():
    return jsonify({"status": "ok", "message": "Issue Tracker API is running"})

@app.get("/stores")
def get_stores():
    return jsonify(STORES)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
