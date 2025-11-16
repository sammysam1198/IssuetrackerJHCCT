import os
import json
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# --- File paths for stores.json (store metadata only) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORES_PATH = os.path.join(BASE_DIR, "Stores.json")

# --- Database connection ---
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Create issues table if it doesn't exist."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id SERIAL PRIMARY KEY,
            store_name TEXT NOT NULL,
            store_number INTEGER,
            issue_name TEXT,
            priority TEXT,
            computer_number TEXT,
            device_type TEXT,
            description TEXT,
            narrative TEXT,
            replicable TEXT,
            status TEXT,
            resolution TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def load_stores():
    with open(STORES_PATH, "r") as f:
        return json.load(f)


@app.get("/")
def home():
    return jsonify({"status": "ok", "message": "Issue Tracker API is running"})


@app.get("/stores")
def get_stores():
    """Return store metadata from Stores.json (no issues here)."""
    stores = load_stores()
    return jsonify(stores)


@app.post("/issues")
def add_issue():
    """
    Add a new issue to the database.

    Expected JSON body:
    {
      "store_name": "Store 123 - Main St",
      "issue": {
        "Issue Name": "...",
        "Priority": "...",
        "Store Number": "123",
        "Computer Number": "PC-01",
        "Type": "Computer",
        "Description": "...",
        "Narrative": "",
        "Replicable?": "Yes/No",
        "Status": "Unresolved",
        "Resolution": ""
      }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    store_name = data.get("store_name")
    issue = data.get("issue")

    if not store_name or not issue:
        return jsonify({"error": "store_name and issue are required"}), 400

    # Pull fields out of the issue dict
    store_number = issue.get("Store Number")
    issue_name = issue.get("Issue Name")
    priority = issue.get("Priority")
    computer_number = issue.get("Computer Number")
    device_type = issue.get("Type")
    description = issue.get("Description")
    narrative = issue.get("Narrative", "")
    replicable = issue.get("Replicable?")
    status = issue.get("Status")
    resolution = issue.get("Resolution", "")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO issues (
            store_name, store_number, issue_name, priority,
            computer_number, device_type, description, narrative,
            replicable, status, resolution
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """,
        (
            store_name,
            int(store_number) if store_number is not None else None,
            issue_name,
            priority,
            computer_number,
            device_type,
            description,
            narrative,
            replicable,
            status,
            resolution,
        ),
    )
    new_issue = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Issue added", "issue": new_issue}), 201


@app.get("/issues/by-store")
def get_issues_by_store():
    """
    Get issues for a specific store.

    Query params:
      ?store_number=123   OR   ?store_name=Store%20123...

    Returns a list of issues from the DB.
    """
    store_number = request.args.get("store_number")
    store_name = request.args.get("store_name")

    if not store_number and not store_name:
        return jsonify({"error": "store_number or store_name is required"}), 400

    conn = get_db_conn()
    cur = conn.cursor()

    if store_number:
        cur.execute(
            """
            SELECT * FROM issues
            WHERE store_number = %s
            ORDER BY id;
            """,
            (int(store_number),),
        )
    else:
        cur.execute(
            """
            SELECT * FROM issues
            WHERE store_name = %s
            ORDER BY id;
            """,
            (store_name,),
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows), 200


@app.post("/issues/update")
def update_issue():
    """
    Update an existing issue in the DB.

    Expected JSON body:
    {
      "issue_id": 123,
      "updated_issue": { ...same fields as add_issue... }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    issue_id = data.get("issue_id")
    updated_issue = data.get("updated_issue")

    if issue_id is None or updated_issue is None:
        return jsonify({"error": "issue_id and updated_issue are required"}), 400

    # Pull updated fields
    store_name = updated_issue.get("Store Name") or updated_issue.get("Store_Name")  # optional
    store_number = updated_issue.get("Store Number")
    issue_name = updated_issue.get("Issue Name")
    priority = updated_issue.get("Priority")
    computer_number = updated_issue.get("Computer Number")
    device_type = updated_issue.get("Type")
    description = updated_issue.get("Description")
    narrative = updated_issue.get("Narrative", "")
    replicable = updated_issue.get("Replicable?")
    status = updated_issue.get("Status")
    resolution = updated_issue.get("Resolution", "")

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE issues
        SET
            store_name = COALESCE(%s, store_name),
            store_number = COALESCE(%s, store_number),
            issue_name = %s,
            priority = %s,
            computer_number = %s,
            device_type = %s,
            description = %s,
            narrative = %s,
            replicable = %s,
            status = %s,
            resolution = %s,
            updated_at = NOW()
        WHERE id = %s
        RETURNING *;
        """,
        (
            store_name,
            int(store_number) if store_number is not None else None,
            issue_name,
            priority,
            computer_number,
            device_type,
            description,
            narrative,
            replicable,
            status,
            resolution,
            issue_id,
        ),
    )
    updated_row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated_row:
        return jsonify({"error": "Issue not found"}), 404

    return jsonify({"message": "Issue updated", "issue": updated_row}), 200

@app.post("/issues/delete")
def delete_issue():
    """
    Delete an existing issue from the DB.

    Expected JSON body:
    {
      "issue_id": 123
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    issue_id = data.get("issue_id")
    if issue_id is None:
        return jsonify({"error": "issue_id is required"}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM issues WHERE id = %s RETURNING *;",
        (issue_id,),
    )
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        return jsonify({"error": "Issue not found"}), 404

    return jsonify({"message": "Issue deleted", "issue": deleted}), 200

# Initialize DB schema when the app starts (works with gunicorn)
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
