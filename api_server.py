import os
import json
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

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
    """Create issues table if it doesn't exist and ensure new columns exist."""
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
            category TEXT,
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
    # In case the table already existed without 'category', add it.
    cur.execute("ALTER TABLE issues ADD COLUMN IF NOT EXISTS category TEXT;")

# ----- NEW: USERS TABLE -----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            password_hash TEXT,
            pin_hash TEXT,
            has_password BOOLEAN NOT NULL DEFAULT FALSE,
            has_pin BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    
    conn.commit()
    cur.close()
    conn.close()
# ------------------------
# PASSWORD HASHING
# ------------------------
def hash_secret(plain: str) -> str:
    """Hash a password or PIN using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")
#SECRET MEANS LIKE A PASSWORD OR PIN IT'S LIKE AN AUTH KEY

def verify_secret(plain: str, stored_hash: str) -> bool:
    """Check if plain password/PIN matches stored bcrypt hash."""
    if not stored_hash:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        return False


SPECIAL_CHARS = set('!@#$%^&*":><')


def check_password_policy(password: str, username: str):
    """Return (ok: bool, errors: list[str]) based on your rules."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if password.lower() == username.lower():
        errors.append("Password cannot be the same as your username.")
    if not any(ch.isupper() for ch in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(ch.islower() for ch in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(ch.isdigit() for ch in password):
        errors.append("Password must contain at least one number.")
    if not any(ch in SPECIAL_CHARS for ch in password):
        errors.append("Password must contain at least one special character (! @ # $ % ^&*\":><).")

    return len(errors) == 0, errors


def check_pin_policy(pin: str):
    """Simple PIN rule: 4–6 digits only."""
    if not pin.isdigit():
        return False, "PIN must contain only digits."
    if not (4 <= len(pin) <= 6):
        return False, "PIN must be between 4 and 6 digits."
    if len(set(pin)) == 1:
        return False, "PIN cannot be all one digit (e.g., 0000, 1111)."

        
    return True, None


def load_stores():
    with open(STORES_PATH, "r") as f:
        return json.load(f)


# -----------------------------------------
#             ENDPOINTS
# -----------------------------------------


@app.get("/")
def home():
    return jsonify({"status": "ok", "message": "Issue Tracker API is running"})


@app.get("/stores")
def get_stores():
    """Return store metadata from Stores.json (no issues here)."""
    stores = load_stores()
    return jsonify(stores)

@app.post("/auth/register")
def auth_register():
    """
    Create or update a user with hashed password and PIN.

    Expected JSON body:
    {
      "email": "Sammi.Fishbein@jtax.com",
      "username": "FishbeinS",
      "password": "MyNewPassword123!",
      "pin": "1234"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    pin = data.get("pin", "")

    if not email or not username or not password or not pin:
        return jsonify({"error": "email, username, password, and pin are required"}), 400

    # Optional: enforce corporate domains here
    lowered = email.lower()
    if not (lowered.endswith("@jtax.com") or lowered.endswith("@jacksonhewittcoo.com")):
        return jsonify({"error": "Email domain not allowed"}), 403

    # Normalize username for policy
    username_norm = username

    # Check password + PIN rules
    ok_pw, pw_errors = check_password_policy(password, username_norm)
    if not ok_pw:
        return jsonify({"error": "Password does not meet requirements", "details": pw_errors}), 400

    ok_pin, pin_error = check_pin_policy(pin)
    if not ok_pin:
        return jsonify({"error": "PIN does not meet requirements", "details": [pin_error]}), 400

    pw_hash = hash_secret(password)
    pin_hash = hash_secret(pin)

    conn = get_db_conn()
    cur = conn.cursor()

    # Upsert-like behavior: if email exists, update; otherwise insert.
    cur.execute(
        """
        INSERT INTO users (email, username, password_hash, pin_hash, has_password, has_pin)
        VALUES (%s, %s, %s, %s, TRUE, TRUE)
        ON CONFLICT (email)
        DO UPDATE SET
            username = EXCLUDED.username,
            password_hash = EXCLUDED.password_hash,
            pin_hash = EXCLUDED.pin_hash,
            has_password = TRUE,
            has_pin = TRUE,
            updated_at = NOW();
        """,
        (email.lower(), username_norm, pw_hash, pin_hash),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "User registered/updated successfully."}), 200


@app.post("/auth/login")
def auth_login():
    """
    Verify email + username + password + PIN.

    Expected JSON:
    {
      "email": "Sammi.Fishbein@jtax.com",
      "username": "FishbeinS",
      "password": "MyNewPassword123!",
      "pin": "1234"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = data.get("email", "").strip().lower()
    username = data.get("username", "")
    password = data.get("password", "")
    pin = data.get("pin", "")

    if not email or not username or not password or not pin:
        return jsonify({"error": "email, username, password, and pin are required"}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT email, username, password_hash, pin_hash, has_password, has_pin
        FROM users
        WHERE email = %s;
        """,
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "No user found with that email"}), 404

    if row["username"] != username:
        return jsonify({"error": "Unable to log in at this time"}), 401

    if not row["has_password"] or not row["password_hash"]:
        return jsonify({"error": "Password not set! Contact Admin"}), 403

    if not verify_secret(password, row["password_hash"]):
        return jsonify({"error": "Unable to log in at this time"}), 401

    if not row["has_pin"] or not row["pin_hash"]:
        return jsonify({"error": "PIN not set! Contact Admin"}), 403

    if not verify_secret(pin, row["pin_hash"]):
        return jsonify({"error": "Unable to log in at this time"}), 401

    # If we get here, everything is good
    return jsonify({"message": "Login successful"}), 200


@app.post("/auth/change-password")
def auth_change_password():
    """
    Change a user's password.

    Expected JSON:
    {
      "email": "user@jtax.com",
      "username": "ExactCaseUsername",
      "current_password": "OldPass123!",
      "new_password": "NewPass123!",
      "pin": "1234"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    pin = data.get("pin", "")

    if not email or not username or not current_password or not new_password or not pin:
        return jsonify(
            {"error": "email, username, current_password, new_password, and pin are required"}
        ), 400

    # Look up user
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT email, username, password_hash, pin_hash, has_password, has_pin
        FROM users
        WHERE email = %s;
        """,
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Unable to change password at this time"}), 401

    # Username must match EXACTLY (case-sensitive)
    if row["username"] != username:
        return jsonify({"error": "Unable to change password at this time"}), 401

    # Must have password/PIN set
    if not row["has_password"] or not row["password_hash"]:
        return jsonify({"error": "Password not set! Contact Admin"}), 403
    if not row["has_pin"] or not row["pin_hash"]:
        return jsonify({"error": "PIN not set! Contact Admin"}), 403

    # Verify current password + PIN
    if not verify_secret(current_password, row["password_hash"]):
        return jsonify({"error": "Unable to change password at this time"}), 401
    if not verify_secret(pin, row["pin_hash"]):
        return jsonify({"error": "Unable to change password at this time"}), 401

    # Check new password policy
    ok_pw, pw_errors = check_password_policy(new_password, username)
    if not ok_pw:
        return jsonify(
            {"error": "New password does not meet requirements", "details": pw_errors}
        ), 400

    # Hash and update
    new_pw_hash = hash_secret(new_password)

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET password_hash = %s,
            has_password = TRUE,
            updated_at = NOW()
        WHERE email = %s;
        """,
        (new_pw_hash, email),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Password changed successfully"}), 200




@app.post("/auth/change-pin")
def auth_change_pin():
    """
    Change a user's PIN.

    Expected JSON:
    {
      "email": "user@jtax.com",
      "username": "ExactCaseUsername",
      "password": "CurrentPassword123!",
      "current_pin": "1234",
      "new_pin": "5678"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    current_pin = data.get("current_pin", "")
    new_pin = data.get("new_pin", "")

    if not email or not username or not password or not current_pin or not new_pin:
        return jsonify(
            {"error": "email, username, password, current_pin, and new_pin are required"}
        ), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT email, username, password_hash, pin_hash, has_password, has_pin
        FROM users
        WHERE email = %s;
        """,
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Unable to change PIN at this time"}), 401

    if row["username"] != username:
        return jsonify({"error": "Unable to change PIN at this time"}), 401

    if not row["has_password"] or not row["password_hash"]:
        return jsonify({"error": "Password not set! Contact Admin"}), 403
    if not row["has_pin"] or not row["pin_hash"]:
        return jsonify({"error": "PIN not set! Contact Admin"}), 403

    # Verify current password + current PIN
    if not verify_secret(password, row["password_hash"]):
        return jsonify({"error": "Unable to change PIN at this time"}), 401
    if not verify_secret(current_pin, row["pin_hash"]):
        return jsonify({"error": "Unable to change PIN at this time"}), 401

    # Check new PIN policy
    ok_pin, pin_error = check_pin_policy(new_pin)
    if not ok_pin:
        return jsonify(
            {"error": "New PIN does not meet requirements", "details": [pin_error]}
        ), 400

    # Hash and update
    new_pin_hash = hash_secret(new_pin)

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET pin_hash = %s,
            has_pin = TRUE,
            updated_at = NOW()
        WHERE email = %s;
        """,
        (new_pin_hash, email),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "PIN changed successfully"}), 200



@app.post("/issues")
def add_issue():
    """
    Add a new issue to the database.

    Expected JSON body:
    {
      "store_name": "Store 123 - Main St",
      "issue": {
        "Name": "...",              # or "Issue Name"
        "Priority": "...",
        "Store Number": "12345",
        "Computer Number": "PC-01",
        "Device": "Computer",       # <--- device type
        "Category": "Hardware",     # <--- problem category
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
    issue_name = issue.get("Name") or issue.get("Issue Name")
    priority = issue.get("Priority")
    computer_number = issue.get("Computer Number")
    device_type = issue.get("Device")          # <--- NEW
    category = issue.get("Category")           # <--- NEW
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
            computer_number, device_type, category,
            description, narrative, replicable, status, resolution
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """,
        (
            store_name,
            int(store_number) if store_number is not None else None,
            issue_name,
            priority,
            computer_number,
            device_type,
            category,
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
      "updated_issue": {
          "Store Name": "...",
          "Store Number": "12345",
          "Name": "...", or "Issue Name": "...",
          "Priority": "...",
          "Computer Number": "...",
          "Device": "Computer",
          "Category": "Hardware",
          "Description": "...",
          "Narrative": "...",
          "Replicable?": "...",
          "Status": "...",
          "Resolution": "..."
      }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    issue_id = data.get("issue_id")
    updated_issue = data.get("updated_issue")

    if issue_id is None or updated_issue is None:
        return jsonify({"error": "issue_id and updated_issue are required"}), 400

    store_name = updated_issue.get("Store Name") or updated_issue.get("Store_Name")
    store_number = updated_issue.get("Store Number")
    issue_name = updated_issue.get("Name") or updated_issue.get("Issue Name")
    priority = updated_issue.get("Priority")
    computer_number = updated_issue.get("Computer Number")
    device_type = updated_issue.get("Device")
    category = updated_issue.get("Category")
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
            category = %s,
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
            category,
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

@app.get("/issues/search")
def search_issues():
    """
    Advanced search for issues.

    Query params (all optional, at least one required):
      store_number=12345
      category=some_text
      status=Unresolved
      device=Computer
      name=Printer%20Down

    All text fields use ILIKE '%value%' (case-insensitive, partial match).
    """
    store_number = request.args.get("store_number")
    category = request.args.get("category")   # maps to device_type
    status = request.args.get("status")
    device = request.args.get("device")       # also maps to device_type
    name = request.args.get("name")           # maps to issue_name

    if not any([store_number, category, status, device, name]):
        return jsonify({"error": "At least one search parameter is required"}), 400

    conn = get_db_conn()
    cur = conn.cursor()

    query = "SELECT * FROM issues WHERE 1=1"
    params = []

    if store_number:
        query += " AND store_number = %s"
        params.append(int(store_number))

    # In your current schema, 'category' and 'device' both map to device_type.
    if category:
        query += " AND category ILIKE %s"
        params.append(f"%{category}%")
    
    if status:
        query += " AND status ILIKE %s"
        params.append(f"%{status}%")

    if device:
        query += " AND device_type ILIKE %s"
        params.append(f"%{device}%")

    if name:
        query += " AND issue_name ILIKE %s"
        params.append(f"%{name}%")

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows), 200


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
