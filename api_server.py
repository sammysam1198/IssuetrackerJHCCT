import os
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORES_PATH = os.path.join(BASE_DIR, "Stores.json")

def load_stores():
    with open(STORES_PATH, "r") as f:
        return json.load(f)

def save_stores(stores):
    with open(STORES_PATH, "w") as f:
        json.dump(stores, f, indent=4)

@app.get("/")
def home():
    return jsonify({"status": "ok", "message": "Issue Tracker API is running"})

@app.get("/stores")
def get_stores():
    # always read the latest data from the file
    stores = load_stores()
    return jsonify(stores)

@app.post("/issues")
def add_issue():
    """
    Body should look like:
    {
      "store_name": "Some Store Name",
      "issue": { ... issue dict ... }
    }
    """
    data = request.get_json(silent=True)
    if not data or "store_name" not in data or "issue" not in data:
        return jsonify({"error": "store_name and issue are required"}), 400

    store_name = data["store_name"]
    issue = data["issue"]

    stores = load_stores()

    if store_name not in stores:
        return jsonify({"error": "Store not found"}), 404

    if "Known Issues" not in stores[store_name]:
        stores[store_name]["Known Issues"] = []

    stores[store_name]["Known Issues"].append(issue)
    save_stores(stores)

    return jsonify(issue), 201  # created

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
