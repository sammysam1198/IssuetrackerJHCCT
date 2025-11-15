import os
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

# --- File paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORES_PATH = os.path.join(BASE_DIR, "Stores.json")


# --- Helper functions ---

def load_stores():
    """Load the Stores.json file from disk."""
    with open(STORES_PATH, "r") as f:
        return json.load(f)


def save_stores(stores):
    """Save the Stores.json file back to disk."""
    with open(STORES_PATH, "w") as f:
        json.dump(stores, f, indent=4)


# --- Routes ---

@app.get("/")
def home():
    return jsonify({"status": "ok", "message": "Issue Tracker API is running"})


@app.get("/stores")
def get_stores():
    """
    Return the current Stores.json contents.
    Your client uses this for validation, searching, etc.
    """
    stores = load_stores()
    return jsonify(stores)


@app.post("/issues")
def add_issue():
    """
    Add a new issue to a specific store.

    Expected JSON body:
    {
      "store_name": "Some Store Name",
      "issue": { ... issue dict ... }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    store_name = data.get("store_name")
    issue = data.get("issue")

    if not store_name or not issue:
        return jsonify({"error": "store_name and issue are required"}), 400

    stores = load_stores()

    if store_name not in stores:
        return jsonify({"error": f"Store '{store_name}' not found"}), 404

    # Ensure Known Issues list exists
    if "Known Issues" not in stores[store_name]:
        stores[store_name]["Known Issues"] = []

    stores[store_name]["Known Issues"].append(issue)
    save_stores(stores)

    return jsonify({"message": "Issue added", "issue": issue}), 201


@app.post("/issues/update")
def update_issue():
    """
    Update an existing issue for a specific store, by index.

    Expected JSON body:
    {
      "store_name": "Some Store Name",
      "issue_index": 0,
      "updated_issue": { ... updated issue dict ... }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    store_name = data.get("store_name")
    issue_index = data.get("issue_index")
    updated_issue = data.get("updated_issue")

    # Basic validation
    if store_name is None or issue_index is None or updated_issue is None:
        return jsonify({"error": "store_name, issue_index, and updated_issue are required"}), 400

    # Load data
    stores = load_stores()

    if store_name not in stores:
        return jsonify({"error": f"Store '{store_name}' not found"}), 404

    known_issues = stores[store_name].get("Known Issues", [])

    if not isinstance(issue_index, int) or issue_index < 0 or issue_index >= len(known_issues):
        return jsonify({"error": "issue_index out of range"}), 400

    # Perform the update
    known_issues[issue_index] = updated_issue
    stores[store_name]["Known Issues"] = known_issues

    # Save back to disk
    save_stores(stores)

    return jsonify({
        "message": "Issue updated",
        "store_name": store_name,
        "issue_index": issue_index,
        "updated_issue": updated_issue
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
