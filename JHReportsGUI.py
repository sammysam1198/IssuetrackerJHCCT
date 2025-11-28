import os
import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, filedialog
from datetime import datetime


# Pillow is optional – used for the logo
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ----------------------------
# THEME
# ----------------------------

JH_PURPLE = "#3C1361"
JH_WHITE_TEXT = "white"

# ----------------------------
# API CONFIG
# ----------------------------

API_BASE = "https://api-server-jh.onrender.com"

stores_cache = None

# --- Admin / auth config ---

TRUSTED_ADMINS = {
    "Sammi.fishbein@jtax.com",
    "John.Maron@jtax.com",
}

# Remember last-logged-in username for quick login autofill
LAST_USER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jh_last_user.txt")

def is_trusted_admin(email: str) -> bool:
    if not email:
        return False
    return email.strip().lower() in {e.lower() for e in TRUSTED_ADMINS}

def api_admin_verify(email: str, password: str, pin: str):
    """
    POST /admin/verify
    Body: { "email", "password", "pin" }
    Returns (ok: bool, message: str)
    """
    payload = {"email": email, "password": password, "pin": pin}
    try:
        resp = requests.post(f"{API_BASE}/admin/verify", json=payload, timeout=10)
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200 and data.get("ok"):
        return True, data.get("message", "Admin verified.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def api_admin_list_users(admin_email: str, admin_password: str, admin_pin: str):
    """
    POST /admin/users
    Body: { "admin_email", "admin_password", "admin_pin" }
    Expects: { "users": [ { "email", "username", "role", ... }, ... ] }
    """
    payload = {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "admin_pin": admin_pin,
    }
    try:
        resp = requests.post(f"{API_BASE}/admin/users", json=payload, timeout=30)
    except requests.RequestException as e:
        return False, [], f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        return False, [], "Server returned invalid JSON for /admin/users."

    if resp.status_code != 200:
        msg = data.get("error") or resp.text
        return False, [], msg

    return True, data.get("users", []), None


def api_get_all_issues():
    """
    Call GET /issues/all on the API server.

    Returns (ok: bool, rows: list[dict], error: str | None)
    """
    try:
        resp = requests.get(f"{API_BASE}/issues/all", timeout=60)
    except requests.RequestException as e:
        return False, [], f"Error contacting server: {e}"

    if resp.status_code != 200:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except Exception:
            msg = resp.text
        return False, [], f"Server returned {resp.status_code}: {msg}"

    try:
        rows = resp.json()
    except ValueError:
        return False, [], "Server returned invalid JSON."
    if not isinstance(rows, list):
        return False, [], "Server returned unexpected data format."
    return True, rows, None


def api_admin_change_password(
    admin_email: str,
    admin_password: str,
    admin_pin: str,
    target_email: str,
    new_password: str,
):
    """
    POST /admin/change-user-password
    Body: { admin_email, admin_password, admin_pin, target_email, new_password }
    """
    payload = {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "admin_pin": admin_pin,
        "target_email": target_email,
        "new_password": new_password,
    }
    try:
        resp = requests.post(
            f"{API_BASE}/admin/change-user-password", json=payload, timeout=30
        )
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200:
        return True, data.get("message", "User password changed.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def api_admin_change_pin(
    admin_email: str,
    admin_password: str,
    admin_pin: str,
    target_email: str,
    new_pin: str,
):
    """
    POST /admin/change-user-pin
    """
    payload = {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "admin_pin": admin_pin,
        "target_email": target_email,
        "new_pin": new_pin,
    }
    try:
        resp = requests.post(
            f"{API_BASE}/admin/change-user-pin", json=payload, timeout=30
        )
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200:
        return True, data.get("message", "User PIN changed.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def api_admin_delete_user(
    admin_email: str,
    admin_password: str,
    admin_pin: str,
    target_email: str,
):
    """
    POST /admin/delete-user
    """
    payload = {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "admin_pin": admin_pin,
        "target_email": target_email,
    }
    try:
        resp = requests.post(
            f"{API_BASE}/admin/delete-user", json=payload, timeout=30
        )
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200:
        return True, data.get("message", "User deleted.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def api_admin_restart_api(
    admin_email: str,
    admin_password: str,
    admin_pin: str,
):
    """
    POST /admin/restart-api
    """
    payload = {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "admin_pin": admin_pin,
    }
    try:
        resp = requests.post(
            f"{API_BASE}/admin/restart-api", json=payload, timeout=30
        )
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200:
        return True, data.get("message", "API restart requested.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def load_last_username() -> str | None:
    try:
        with open(LAST_USER_FILE, "r", encoding="utf-8") as f:
            username = f.read().strip()
            return username or None
    except FileNotFoundError:
        return None
    except OSError:
        return None


def save_last_username(username: str) -> None:
    username = (username or "").strip()
    if not username:
        return
    try:
        with open(LAST_USER_FILE, "w", encoding="utf-8") as f:
            f.write(username)
    except OSError:
        # If we can't write, just silently ignore
        pass





# ----------------------------
# ASSET PATHS
# ----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_WHITE_PATH = os.path.join(BASE_DIR, "jh_logo_white.png")


# ----------------------------
# API HELPER FUNCTIONS
# ----------------------------

def api_quick_login(username: str, password: str):
    """
    Try quick login with username + password.
    Returns (success: bool, require_full: bool, message: str)
    """
    payload = {"username": username, "password": password}

    try:
        resp = requests.post(f"{API_BASE}/auth/quick-login", json=payload, timeout=10)
    except requests.RequestException as e:
        return False, False, f"Error contacting server: {e}"

    if resp.status_code == 200:
        return True, False, "Quick login successful."

    try:
        data = resp.json()
    except ValueError:
        data = {}

    require_full = bool(data.get("require_full", False))
    msg = data.get("error") or f"Login failed: {resp.status_code}"
    return False, require_full, msg


def api_full_login(email: str, username: str, password: str, pin: str):
    """
    Do full login with email + username + password + PIN.
    Returns (success: bool, message: str)
    """
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "pin": pin,
    }

    try:
        resp = requests.post(f"{API_BASE}/auth/login", json=payload, timeout=10)
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    if resp.status_code == 200:
        return True, "Login successful."
    else:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except ValueError:
            msg = resp.text
        return False, f"Login failed: {msg}"


def api_change_password(email: str, username: str, current_password: str, new_password: str, pin: str):
    """
    Call POST /auth/change-password.
    Returns (success: bool, message: str)
    """
    payload = {
        "email": email,
        "username": username,
        "current_password": current_password,
        "new_password": new_password,
        "pin": pin,
    }

    try:
        resp = requests.post(f"{API_BASE}/auth/change-password", json=payload, timeout=15)
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200:
        return True, data.get("message", "Password changed successfully.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def api_change_pin(email: str, username: str, password: str, current_pin: str, new_pin: str):
    """
    Call POST /auth/change-pin.
    Returns (success: bool, message: str)
    """
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "current_pin": current_pin,
        "new_pin": new_pin,
    }

    try:
        resp = requests.post(f"{API_BASE}/auth/change-pin", json=payload, timeout=15)
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if resp.status_code == 200:
        return True, data.get("message", "PIN changed successfully.")
    else:
        msg = data.get("error") or resp.text
        return False, msg


def api_load_stores():
    """
    Load store metadata from the API (from Stores.json on the server).
    Uses a simple in-memory cache.
    Returns (stores: dict | None, error: str | None)
    """
    global stores_cache
    if stores_cache is not None:
        return stores_cache, None

    try:
        resp = requests.get(f"{API_BASE}/stores", timeout=30)
        resp.raise_for_status()
        stores_cache = resp.json()
        return stores_cache, None
    except requests.RequestException as e:
        return None, f"Error loading store list from server: {e}"


def api_add_issue(store_name: str, issue: dict):
    """
    Call POST /issues with the given store_name and legacy-style issue dict.
    Returns (success: bool, message: str)
    """
    payload = {
        "store_name": store_name,
        "issue": issue,
    }

    try:
        resp = requests.post(f"{API_BASE}/issues", json=payload, timeout=60)
        resp.raise_for_status()
        return True, "Issue added and synced to the server."
    except requests.HTTPError:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except Exception:
            msg = resp.text
        return False, f"Server error: {msg}"
    except requests.RequestException as e:
        return False, f"Error sending issue to server: {e}"


def api_search_issues(store_number: int | None = None, name: str | None = None):
    """
    Call GET /issues/search on the API server.

    - If store_number is provided, search by that store.
    - If name is provided, search issue_name with a partial, case-insensitive match.

    Returns (ok: bool, rows: list[dict], error: str | None)
    """
    params: dict[str, str] = {}
    if store_number is not None:
        params["store_number"] = str(store_number)
    if name:
        params["name"] = name

    if not params:
        return False, [], "No search parameters provided."

    try:
        resp = requests.get(f"{API_BASE}/issues/search", params=params, timeout=30)
    except requests.RequestException as e:
        return False, [], f"Error contacting server: {e}"

    if resp.status_code != 200:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except ValueError:
            msg = resp.text
        return False, [], f"Search failed: {msg}"

    try:
        rows = resp.json()
    except ValueError:
        return False, [], "Server returned invalid JSON for /issues/search"

    if not isinstance(rows, list):
        return False, [], "Search response was not a list."

    return True, rows, None


def api_update_issue(issue_id: int, updated_issue: dict):
    """
    Call POST /issues/update to update an existing issue in the DB.

    Expected by the API:
    {
      "issue_id": 123,
      "updated_issue": { ...same keys as add_issue 'issue' payload... }
    }

    Returns (success: bool, message: str)
    """
    payload = {
        "issue_id": issue_id,
        "updated_issue": updated_issue,
    }

    try:
        resp = requests.post(f"{API_BASE}/issues/update", json=payload, timeout=30)
    except requests.RequestException as e:
        return False, f"Error contacting server: {e}"

    if resp.status_code == 200:
        return True, "Issue updated successfully."
    else:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except ValueError:
            msg = resp.text
        return False, f"Update failed: {msg}"

def api_get_stores():
    """
    Fetch store metadata from /stores.
    Returns (ok: bool, stores: dict, error: str | None)
    """
    global stores_cache

    if stores_cache is not None:
        return True, stores_cache, None

    try:
        resp = requests.get(f"{API_BASE}/stores", timeout=30)
    except requests.RequestException as e:
        return False, {}, f"Error contacting server: {e}"

    if resp.status_code != 200:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except ValueError:
            msg = resp.text
        return False, {}, f"Failed to load stores: {msg}"

    try:
        stores = resp.json()
    except ValueError:
        return False, {}, "Server returned invalid JSON for /stores"

    if not isinstance(stores, dict):
        return False, {}, "Stores response was not a JSON object."

    stores_cache = stores
    return True, stores, None


def api_get_issues_by_store(store_number: int | None = None, store_name: str | None = None,):
    """
    Call GET /issues/by-store on the API server.

    Exactly one of store_number or store_name should be provided.

    Returns (ok: bool, rows: list[dict], error: str | None)
    """
    params: dict[str, str] = {}
    if store_number is not None:
        params["store_number"] = str(store_number)
    if store_name:
        params["store_name"] = store_name

    if not params:
        return False, [], "store_number or store_name is required."

    try:
        resp = requests.get(f"{API_BASE}/issues/by-store", params=params, timeout=30)
    except requests.RequestException as e:
        return False, [], f"Error contacting server: {e}"

    if resp.status_code != 200:
        try:
            data = resp.json()
            msg = data.get("error") or resp.text
        except ValueError:
            msg = resp.text
        return False, [], f"Failed to load issues: {msg}"

    try:
        rows = resp.json()
    except ValueError:
        return False, [], "Server returned invalid JSON for /issues/by-store"

    if not isinstance(rows, list):
        return False, [], "Issues response was not a list."

    return True, rows, None

# ----------------------------
# BASE PURPLE FRAME
# ----------------------------

class PurpleFrame(tk.Frame):
    """
    Base class for all screens – sets JH purple background,
    and helpers for on-brand labels/frames.
    """
    def __init__(self, parent, *args, **kwargs):
        kwargs.setdefault("bg", JH_PURPLE)
        super().__init__(parent, *args, **kwargs)

    @staticmethod
    def label(parent, text, **kwargs):
        """Create a white-on-purple label on any parent frame."""
        kw = {"text": text, "fg": JH_WHITE_TEXT, "bg": JH_PURPLE}
        kw.update(kwargs)
        return tk.Label(parent, **kw)

    @staticmethod
    def subframe(parent, **kwargs):
        """Create a purple background frame inside any parent."""
        kw = {"bg": JH_PURPLE}
        kw.update(kwargs)
        return tk.Frame(parent, **kw)


# ----------------------------
# LOGIN FRAME
# ----------------------------

class LoginFrame(PurpleFrame):
    """Purple-themed login screen."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        title = PurpleFrame.label(self, "JH Reports – Login", font=("Segoe UI", 22, "bold"))
        title.pack(pady=25)

        form_frame = PurpleFrame.subframe(self)
        form_frame.pack(pady=10)

        lbl = {"fg": JH_WHITE_TEXT, "bg": JH_PURPLE, "font": ("Segoe UI", 11)}
        entry_width = 30

        tk.Label(form_frame, text="Username:", **lbl).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.entry_username = tk.Entry(form_frame, width=entry_width)
        self.entry_username.grid(row=0, column=1, pady=5, padx=5)

        # Autofill last logged-in username, if available
        last_user = load_last_username()
        if last_user:
            self.entry_username.insert(0, last_user)


        tk.Label(form_frame, text="Password:", **lbl).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.entry_password = tk.Entry(form_frame, show="*", width=entry_width)
        self.entry_password.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(form_frame, text="Email (if needed):", **lbl).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.entry_email = tk.Entry(form_frame, width=entry_width)
        self.entry_email.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(form_frame, text="PIN (if needed):", **lbl).grid(row=3, column=0, sticky="e", pady=5, padx=5)
        self.entry_pin = tk.Entry(form_frame, show="*", width=entry_width)
        self.entry_pin.grid(row=3, column=1, pady=5, padx=5)

        self.status_label = PurpleFrame.label(self, "", font=("Segoe UI", 10))
        self.status_label.pack(pady=5)

        btn_frame = PurpleFrame.subframe(self)
        btn_frame.pack(pady=10)

        self.login_button = tk.Button(btn_frame, text="Log In", width=12, command=self.handle_login)
        self.login_button.grid(row=0, column=0, padx=10)

        quit_button = tk.Button(btn_frame, text="Quit", width=12, command=self.controller.destroy)
        quit_button.grid(row=0, column=1, padx=10)

        # Forgot Password helper
        forgot_btn = tk.Button(
            btn_frame,
            text="Forgot Password",
            width=26,
            command=self.show_forgot_password,
        )
        forgot_btn.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        self.bind("<Return>", self._enter_login)

    def handle_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get()

        if not username or not password:
            messagebox.showerror("Login Error", "Username and password are required.")
            return

        self.status_label.config(text="Attempting quick login...")
        self.login_button.config(state="disabled")
        self.update_idletasks()

        # Quick login attempt
        success, require_full, msg = api_quick_login(username, password)

        if success:
            # If they typed an email, use it so we can detect trusted admins
            email = self.entry_email.get().strip() or None
            self.controller.set_user(username=username, email=email)
            save_last_username(username)
            messagebox.showinfo("Login", "Quick login successful.")
            self.controller.show_frame("MainMenuFrame")
            self.login_button.config(state="normal")
            self.status_label.config(text="")
            return

        # If API says full login is needed
        if require_full:
            self.status_label.config(text="Quick login requires full login...")

            email = self.entry_email.get().strip()
            pin = self.entry_pin.get().strip()

            if not email or not pin:
                messagebox.showwarning(
                    "Full Login Required",
                    "Quick login failed. Please enter your email and PIN, then click Log In again."
                )
                self.login_button.config(state="normal")
                return

            success_full, msg_full = api_full_login(email, username, password, pin)
            if success_full:
                self.controller.set_user(username=username, email=email)
                save_last_username(username)
                messagebox.showinfo("Login", "Full login successful.")
                self.controller.show_frame("MainMenuFrame")
                self.status_label.config(text="")
            else:
                messagebox.showerror("Login Failed", msg_full)
                self.status_label.config(text=msg_full)

            self.login_button.config(state="normal")
            return

        # Quick login failed for another reason
        messagebox.showerror("Login Failed", msg)
        self.status_label.config(text=msg)
        self.login_button.config(state="normal")


    def show_forgot_password(self):
        message = (
            "Call or Email Project Dev Sammi Fishbein for immediate authentication services.\n\n"
            "Email: sammi.fishbein@jtax.com\n"
            "Phone: 1-(978)-729-7544"
        )
        messagebox.showinfo("Forgot Password", message)

    def _enter_login(self, event):
        self.handle_login()


# ----------------------------
# MAIN MENU FRAME
# ----------------------------

class MainMenuFrame(PurpleFrame):
    """
    JH Purple background
    Buttons on LEFT
    White JH logo on RIGHT
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        # Load logo
        self.logo_image = None
        self.logo_label = tk.Label(self, bg=JH_PURPLE)
        self.load_logo()

        # LEFT CONTENT FRAME
        content_frame = PurpleFrame.subframe(self, padx=20, pady=20)
        content_frame.pack(side="left", fill="y")

        title = PurpleFrame.label(
            content_frame,
            "JH Reports – Main Menu",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(anchor="w", pady=(10, 5))

        # Logged in user
        self.user_label = PurpleFrame.label(
            content_frame,
            "Logged in as:",
            font=("Segoe UI", 10),
        )
        self.user_label.pack(anchor="w", pady=(0, 20))

        # BUTTON LIST
        btn_frame = PurpleFrame.subframe(content_frame)
        btn_frame.pack(anchor="w")

        buttons = [
            ("Report Issue", lambda: self.controller.show_frame("ReportIssueFrame")),
            ("Edit Issue", lambda: self.controller.show_frame("EditIssueFrame")),
            ("Update Status", self.not_implemented_yet),
            ("View Issues (One Store)", lambda: self.controller.show_frame("ViewOneStoreFrame")),
            ("View All Issues", lambda: self.controller.show_frame("ViewAllIssuesFrame")),
            ("Search Issues", self.not_implemented_yet),
            ("Remove Issue", self.not_implemented_yet),
            ("Print All Issues", self.not_implemented_yet),
            ("Utilities", lambda: self.controller.show_frame("UtilitiesFrame"))
        ]

        for label, cmd in buttons:
            tk.Button(btn_frame, text=label, width=25, command=cmd).pack(anchor="w", pady=4)

        # LOGOUT BUTTON
        tk.Button(
            content_frame, text="Log Out", width=18, command=self.handle_logout
        ).pack(anchor="w", pady=(20, 0))

        # Place LOGO on RIGHT side
        self.logo_label.pack(side="right", padx=40)

        self.bind("<<ShowFrame>>", self.on_show_frame)

    def load_logo(self):
        if not PIL_AVAILABLE:
            self.logo_label.configure(text="jh", fg=JH_WHITE_TEXT, bg=JH_PURPLE)
            return
        try:
            img = Image.open(LOGO_WHITE_PATH)
            img.thumbnail((240, 240))
            self.logo_image = ImageTk.PhotoImage(img)
            self.logo_label.configure(image=self.logo_image)
        except Exception:
            self.logo_label.configure(text="jh", fg=JH_WHITE_TEXT, bg=JH_PURPLE)

    def on_show_frame(self, event=None):
        username = self.controller.current_username or "Unknown"
        email = self.controller.current_email
        if email:
            self.user_label.config(text=f"Logged in as: {username} ({email})")
        else:
            self.user_label.config(text=f"Logged in as: {username}")

    def handle_logout(self):
        self.controller.set_user(None, None)
        self.controller.show_frame("LoginFrame")

    def not_implemented_yet(self):
        messagebox.showinfo("Coming soon", "Feature not finished yet.")


# ----------------------------
# UTILITIES/MENU FRAME(S)
# ----------------------------

class UtilitiesFrame(PurpleFrame):
    """
    Utilities submenu:
    - Store Search
    - Tech Info By Store (TODO)
    - Change Password
    - Change PIN
    - Admin Tools
    - Back to Main Menu
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        title = PurpleFrame.label(
            self,
            "Utilities",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=25)

        btn_frame = PurpleFrame.subframe(self)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Store Lookup",
            width=25,
            command=lambda: self.controller.show_frame("StoreSearchFrame"),
        ).pack(pady=4)

        tk.Button(
            btn_frame,
            text="Tech Info By Store",
            width=25,
            command=self.tech_info_not_ready,
        ).pack(pady=4)

        tk.Button(
            btn_frame,
            text="Change Password",
            width=25,
            command=lambda: self.controller.show_frame("ChangePasswordFrame"),
        ).pack(pady=4)

        tk.Button(
            btn_frame,
            text="Change PIN",
            width=25,
            command=lambda: self.controller.show_frame("ChangePINFrame"),
        ).pack(pady=4)

        # 🔐 Admin Tools button (packed conditionally in on_show_frame)
        self.admin_button = tk.Button(
            btn_frame,
            text="Admin Tools",
            width=25,
            command=lambda: self.controller.show_frame("AdminToolsFrame"),
        )
        self._admin_btn_packed = False

        tk.Button(
            btn_frame,
            text="Back to Main Menu",
            width=25,
            command=lambda: self.controller.show_frame("MainMenuFrame"),
        ).pack(pady=(12, 4))

        self.bind("<<ShowFrame>>", self.on_show_frame)

    def on_show_frame(self, event=None):
        # Show Admin Tools only if current user is trusted admin
        if self.controller.is_admin:
            if not self._admin_btn_packed:
                self.admin_button.pack(pady=4)
                self._admin_btn_packed = True
        else:
            if self._admin_btn_packed:
                self.admin_button.pack_forget()
                self._admin_btn_packed = False

    def tech_info_not_ready(self):
        messagebox.showinfo(
            "Tech Info By Store",
            "This feature is not implemented yet.\n\n"
            "Once the hardware/software inventory DB is ready, it can be wired here.",
        )

class AdminToolsFrame(PurpleFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        # ============ TOP TITLE ==============
        title = PurpleFrame.label(
            self, "Admin Tools", font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=20)

        # ============ MAIN HORIZONTAL SPLIT FRAME =============
        main_frame = tk.Frame(self, bg=JH_PURPLE)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # LEFT COLUMN (buttons)
        left_frame = tk.Frame(main_frame, bg=JH_PURPLE)
        left_frame.pack(side="left", fill="y", padx=(0, 20))

        # RIGHT COLUMN (text area + export buttons)
        right_frame = tk.Frame(main_frame, bg=JH_PURPLE)
        right_frame.pack(side="right", fill="both", expand=True)

        # ------------- LEFT BUTTON STACK -------------
        tk.Button(left_frame, text="List Users", width=25,
                  command=self.admin_list_users).pack(pady=4)

        tk.Button(left_frame, text="Create New User", width=25,
            command=self.open_create_user_window).pack(pady=4)

        tk.Button(left_frame, text="List All Store Info", width=25,
                  command=self.admin_list_stores).pack(pady=4)

        tk.Button(left_frame, text="List All Issues", width=25,
                  command=self.admin_list_issues).pack(pady=4)

        PurpleFrame.label(
            left_frame, "Account Management", font=("Segoe UI", 12, "bold")
        ).pack(pady=(12, 4))

        tk.Button(left_frame, text="Admin Change Password", width=25,
                  command=self.admin_change_password).pack(pady=4)

        tk.Button(left_frame, text="Admin Change PIN", width=25,
                  command=self.admin_change_pin).pack(pady=4)

        tk.Button(left_frame, text="Admin Delete User", width=25,
                  command=self.admin_delete_user).pack(pady=4)

        PurpleFrame.label(
            left_frame, "System", font=("Segoe UI", 12, "bold")
        ).pack(pady=(12, 4))

        tk.Button(left_frame, text="Admin Restart API", width=25,
                  command=self.admin_restart_api).pack(pady=4)

        tk.Button(
            left_frame,
            text="Back to Utilities",
            width=25,
            command=lambda: self.controller.show_frame("UtilitiesFrame")
        ).pack(pady=(20, 4))

        # ------------- RIGHT SIDE (TITLE + TEXT) -------------
        self.report_title_label = PurpleFrame.label(
            right_frame, "", font=("Segoe UI", 12, "bold")
        )
        self.report_title_label.pack(pady=(0, 6))

        self.report_text = scrolledtext.ScrolledText(
            right_frame,
            width=80,
            height=25,
            wrap="word",
            bg=JH_PURPLE,
            fg=JH_WHITE_TEXT
        )
        self.report_text.pack(fill="both", expand=True)

        # ------------- BOTTOM OF RIGHT SIDE -------------
        bottom_buttons = tk.Frame(right_frame, bg=JH_PURPLE)
        bottom_buttons.pack(pady=6)

        tk.Button(bottom_buttons, text="Print to Text File", width=18,
                  command=self.export_report_to_file).grid(row=0, column=0, padx=5)

        tk.Button(bottom_buttons, text="Clear Report", width=18,
                  command=self.clear_report).grid(row=0, column=1, padx=5)

        self.current_report_content = ""
        self.current_report_prefix = "admin_report"

        self.bind("<<ShowFrame>>", self.on_show_frame)


    # ---------- Frame lifecycle ----------

    def on_show_frame(self, event=None):
        # If somehow a non-admin gets here, kick them out
        if not self.controller.is_admin:
            messagebox.showwarning(
                "Access Denied",
                "Your account is not in the trusted admin list.",
            )
            self.controller.show_frame("UtilitiesFrame")
            return

        # Start with a clean status/report when entering
        self.clear_report()

    # ---------- Shared helpers ----------

    def _require_admin_credentials(self):
        """
        Verify:
        - a user is logged in
        - email is in TRUSTED_ADMINS
        - password + PIN are verified via /admin/verify

        Returns (email, password, pin) or None if cancelled/failed.
        """
        email = self.controller.current_email
        if not email:
            messagebox.showerror("Error", "No email is associated with this session.")
            return None

        if not is_trusted_admin(email):
            messagebox.showerror("Access Denied", "You are not a trusted admin.")
            return None

        password = simpledialog.askstring(
            "Admin Verification",
            f"Enter password for {email}:",
            show="*",
            parent=self,
        )
        if password is None:
            return None

        pin = simpledialog.askstring(
            "Admin Verification",
            "Enter your admin PIN:",
            show="*",
            parent=self,
        )
        if pin is None:
            return None

        ok, msg = api_admin_verify(email, password, pin)
        if not ok:
            messagebox.showerror("Verification Failed", msg)
            return None

        return email, password, pin

    def _show_report(self, title: str, content: str, prefix: str):
        self.report_title_label.config(text=title)
        self.current_report_content = content
        self.current_report_prefix = prefix

        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("end", content)
        self.report_text.config(state="disabled")

    def clear_report(self):
        self.report_title_label.config(text="")
        self.current_report_content = ""
        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.config(state="disabled")

    def export_report_to_file(self):
        if not self.current_report_content.strip():
            messagebox.showinfo("No Report", "There is no report to print to a file.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested = f"{self.current_report_prefix}_{ts}.txt"

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=suggested,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.current_report_content)
            messagebox.showinfo("Saved", f"Report saved to:\n{path}")
        except OSError as e:
            messagebox.showerror("Error", f"Could not save report:\n{e}")

    # ---------- Admin actions ----------

    def admin_list_users(self):
        creds = self._require_admin_credentials()
        if not creds:
            return
        email, password, pin = creds

        ok, users, error = api_admin_list_users(email, password, pin)
        if not ok:
            messagebox.showerror("Error", error or "Failed to load users.")
            return

        if not users:
            self._show_report("Users", "No users found.\n", "users")
            return

        lines = []
        for u in users:
            lines.append(f"Email: {u.get('email', 'N/A')}")
            lines.append(f"Username: {u.get('username', 'N/A')}")
            lines.append(f"Role: {u.get('role', 'user')}")
            lines.append("----------------------------")
        content = "\n".join(lines) + "\n"
        self._show_report("Users", content, "users")

    def open_create_user_window(self):
        """Open a small admin dialog to create a new user via /auth/register."""
        win = tk.Toplevel(self)
        win.title("Create User")
        win.geometry("400x260")

        # ----- Form fields -----
        tk.Label(win, text="Email:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        email_entry = tk.Entry(win, width=35)
        email_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(win, text="Username:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        username_entry = tk.Entry(win, width=35)
        username_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(win, text="Password:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        password_entry = tk.Entry(win, width=35, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(win, text="Confirm Password:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        confirm_entry = tk.Entry(win, width=35, show="*")
        confirm_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(win, text="PIN (4–6 digits):").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        pin_entry = tk.Entry(win, width=10)
        pin_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # ----- Submit handler -----
        def submit():
            email = email_entry.get().strip()
            username = username_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            pin = pin_entry.get().strip()

            if not email or not username or not password or not confirm or not pin:
                messagebox.showerror("Error", "All fields are required.")
                return

            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            if not pin.isdigit() or not (4 <= len(pin) <= 6):
                messagebox.showerror("Error", "PIN must be 4–6 digits.")
                return

            payload = {
                "email": email,
                "username": username,
                "password": password,
                "pin": pin,
            }

            try:
                resp = requests.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
            except requests.RequestException as e:
                messagebox.showerror("Network Error", f"Error talking to server:\n{e}")
                return

            if resp.status_code == 201:
                messagebox.showinfo("Success", "User created successfully.")
                win.destroy()
            else:
                # Show server response body so you can see validation errors, etc.
                messagebox.showerror(
                    "Error",
                    f"Failed to create user.\nStatus: {resp.status_code}\n\n{resp.text}",
                )

        # ----- Buttons -----
        btn_frame = tk.Frame(win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15)

        tk.Button(btn_frame, text="Create User", command=submit).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=5)

    def admin_list_stores(self):
        creds = self._require_admin_credentials()
        if not creds:
            return

        stores, error = api_load_stores()
        if stores is None:
            messagebox.showerror("Error", error or "Failed to load stores.")
            return

        lines = []
        for name in sorted(stores.keys()):
            details = stores[name]
            lines.append(f"Store Name: {name}")
            lines.append(f"Store Number: {details.get('Store Number', 'N/A')}")
            lines.append(f"Address: {details.get('Address', 'Unknown')}")
            lines.append(
                f"City: {details.get('City', 'Unknown')}  "
                f"State: {details.get('State', 'Unknown')}  "
                f"ZIP: {details.get('ZIP', 'Unknown')}"
            )
            lines.append(f"Phone: {details.get('Phone', 'Unknown')}")
            lines.append(f"Type: {details.get('Type', 'Unknown')}")
            lines.append(f"Kiosk Type: {details.get('Kiosk Type', 'Unknown')}")
            lines.append(f"Computers: {details.get('Computers', 'Unknown')}")
            lines.append("----------------------------")
        content = "\n".join(lines) + "\n"
        self._show_report("All Store Info", content, "stores")

    def admin_list_issues(self):
        creds = self._require_admin_credentials()
        if not creds:
            return

        ok, rows, err = api_get_all_issues()
        if not ok:
            messagebox.showerror("Error", err or "Failed to load issues.")
            return

        if not rows:
            self._show_report("All Issues", "No issues found.\n", "issues")
            return

        lines = []
        total_issues = 0

        # Group by store for prettier output
        from collections import defaultdict
        by_store = defaultdict(list)
        for row in rows:
            key = (row.get("store_name"), row.get("store_number"))
            by_store[key].append(row)

        for (sName, sNum), issue_rows in sorted(
                by_store.items(),
                key=lambda k: (k[0][1] or 0, (k[0][0] or "").lower())
        ):
            if not issue_rows:
                continue

            store_label = sName or "Unknown Store"
            if sNum is not None:
                header = f"{store_label} (Store {sNum})"
            else:
                header = store_label

            lines.append(header)
            lines.append("-" * len(header))

            for idx, row in enumerate(issue_rows, start=1):
                total_issues += 1
                issue_name = row.get("issue_name") or "Unnamed Issue"
                status = row.get("status") or "Unresolved"
                lines.append(f"{idx}. {issue_name} [{status}]")

                device = row.get("device_type") or ""
                if device:
                    lines.append(f"Device: {device}")

                category = row.get("category") or ""
                if category:
                    lines.append(f"Category: {category}")

                comp = row.get("computer_number")
                if comp and str(comp).strip().upper() != "N/A":
                    lines.append(f"Computer: {comp}")

                # Priority prettifier
                priority_raw = row.get("priority")
                pretty_priority = "Unknown"
                if priority_raw is not None:
                    val = str(priority_raw).strip()
                    if val == "1":
                        pretty_priority = "Critical"
                    elif val == "2":
                        pretty_priority = "Functional"
                    elif val == "3":
                        pretty_priority = "Cosmetic"
                    else:
                        pretty_priority = val
                lines.append(f"Priority: {pretty_priority}")

                g_issue = row.get("global_issue")
                if g_issue is not None:
                    lines.append(f"Global issue: {'Yes' if g_issue else 'No'}")
                g_num = row.get("global_num")
                if g_num is not None:
                    lines.append(f"Devices affected: {g_num}")

                desc = row.get("description") or ""
                if desc:
                    lines.append(f"Description:\n{desc}")

                narrative = row.get("narrative") or ""
                if narrative:
                    lines.append(f"Narrative:\n{narrative}")

                resolution = row.get("resolution") or ""
                if resolution:
                    lines.append(f"Resolution:\n{resolution}")

                lines.append("----    ----    ----    ----")
                lines.append("")
            lines.append("")

        content = "\n".join(lines) + f"\n\nTotal issues: {total_issues}\n"
        self._show_report("All Issues", content, "issues")

    def admin_change_password(self):
        creds = self._require_admin_credentials()
        if not creds:
            return
        email, password, pin = creds

        target_email = simpledialog.askstring(
            "Admin Change Password",
            "Enter the user's email to change password:",
            parent=self,
        )
        if not target_email:
            return

        new_pw = simpledialog.askstring(
            "Admin Change Password",
            f"Enter NEW password for {target_email}:",
            show="*",
            parent=self,
        )
        if not new_pw:
            return

        ok, msg = api_admin_change_password(
            email, password, pin, target_email, new_pw
        )
        if ok:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def admin_change_pin(self):
        creds = self._require_admin_credentials()
        if not creds:
            return
        email, password, pin = creds

        target_email = simpledialog.askstring(
            "Admin Change PIN",
            "Enter the user's email to change PIN:",
            parent=self,
        )
        if not target_email:
            return

        new_pin = simpledialog.askstring(
            "Admin Change PIN",
            f"Enter NEW PIN for {target_email}:",
            show="*",
            parent=self,
        )
        if not new_pin:
            return

        ok, msg = api_admin_change_pin(
            email, password, pin, target_email, new_pin
        )
        if ok:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def admin_delete_user(self):
        creds = self._require_admin_credentials()
        if not creds:
            return
        email, password, pin = creds

        target_email = simpledialog.askstring(
            "Admin Delete User",
            "Enter the user's email to DELETE:",
            parent=self,
        )
        if not target_email:
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete user:\n{target_email}?",
        ):
            return

        ok, msg = api_admin_delete_user(
            email, password, pin, target_email
        )
        if ok:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def admin_restart_api(self):
        creds = self._require_admin_credentials()
        if not creds:
            return
        email, password, pin = creds

        if not messagebox.askyesno(
            "Restart API",
            "Are you sure you want to restart the API server?",
        ):
            return

        ok, msg = api_admin_restart_api(email, password, pin)
        if ok:
            messagebox.showinfo("Restart Requested", msg)
        else:
            messagebox.showerror("Error", msg)

class StoreSearchFrame(PurpleFrame):
    """
    GUI version of storeLookup():
    - Enter store NAME or store NUMBER
    - Shows exact match, or partial matches, or "not found"
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        title = PurpleFrame.label(
            self,
            "Store Search",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=20)

        self.status_label = PurpleFrame.label(
            self,
            "",
            font=("Segoe UI", 10),
        )
        self.status_label.pack(pady=(0, 10))

        # Search bar
        search_frame = PurpleFrame.subframe(self)
        search_frame.pack(pady=10, padx=20, fill="x")

        PurpleFrame.label(
            search_frame,
            "Enter store NAME or NUMBER:",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.entry_query = tk.Entry(search_frame, width=40)
        self.entry_query.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tk.Button(
            search_frame,
            text="Search",
            width=12,
            command=self.handle_search,
        ).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Results text
        self.text = scrolledtext.ScrolledText(
            self,
            width=80,
            height=18,
            wrap="word",
            bg=JH_PURPLE,
            fg=JH_WHITE_TEXT,
        )
        self.text.pack(padx=20, pady=10, fill="both", expand=True)

        # Back button
        bottom_frame = PurpleFrame.subframe(self)
        bottom_frame.pack(pady=10)
        tk.Button(
            bottom_frame,
            text="Back to Utilities",
            width=18,
            command=lambda: self.controller.show_frame("UtilitiesFrame"),
        ).pack()

        self.bind("<<ShowFrame>>", self.on_show_frame)



    def on_show_frame(self, event=None):
        self.status_label.config(text="")
        self.entry_query.delete(0, "end")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def handle_search(self):
        query = self.entry_query.get().strip()
        if not query:
            messagebox.showwarning(
                "Input Required",
                "Please enter a store name or number.",
            )
            return

        stores, error = api_load_stores()
        if stores is None:
            self.status_label.config(text=error or "Failed to load stores.")
            messagebox.showerror(
                "Error",
                error or "Failed to load stores from server.",
            )
            return

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        # Try as number first
        if query.isdigit():
            for name, details in stores.items():
                if str(details.get("Store Number")) == query:
                    self.render_store_info(name, details)
                    self.status_label.config(
                        text=f"Found store #{query} – {name}"
                    )
                    self.text.configure(state="disabled")
                    return

            self.status_label.config(text=f"No store found with number {query}.")
            self.text.insert("end", f"No store found with number {query}.\n")
            self.text.configure(state="disabled")
            return

        # Otherwise treat as name (exact match, then partial)
        lowered = query.lower()

        # Exact match
        for name, details in stores.items():
            if name.lower() == lowered:
                self.render_store_info(name, details)
                self.status_label.config(text=f"Found store '{name}'.")
                self.text.configure(state="disabled")
                return

        # Partial matches
        matches = [
            (name, details)
            for name, details in stores.items()
            if lowered in name.lower()
        ]

        if not matches:
            self.status_label.config(text="No matching stores found.")
            self.text.insert("end", "No matching stores found.\n")
            self.text.configure(state="disabled")
            return

        if len(matches) == 1:
            name, details = matches[0]
            self.render_store_info(name, details)
            self.status_label.config(text=f"Found store '{name}'.")
        else:
            self.status_label.config(
                text=f"{len(matches)} stores matched your search."
            )
            self.text.insert(
                "end",
                "Multiple stores matched your search:\n\n",
            )
            for name, details in matches:
                num = details.get("Store Number", "N/A")
                state = details.get("State", "Unknown")
                type_ = details.get("Type", "Unknown")
                self.text.insert(
                    "end",
                    f"- {name} (Store {num}, {state}, {type_})\n",
                )

        self.text.configure(state="disabled")

    def render_store_info(self, name: str, details: dict):
        self.text.insert("end", "Store Information\n")
        self.text.insert("end", "----------------------------\n")
        self.text.insert("end", f"Store Name: {name}\n")
        self.text.insert("end", f"Store Number: {details.get('Store Number', 'N/A')}\n")
        self.text.insert("end", f"Address: {details.get('Address', 'Unknown')}\n")
        self.text.insert("end", f"City: {details.get('City', 'Unknown')}\n")
        self.text.insert("end", f"State: {details.get('State', 'Unknown')}\n")
        self.text.insert("end", f"ZIP: {details.get('ZIP', 'Unknown')}\n")
        self.text.insert("end", f"Phone: {details.get('Phone', 'Unknown')}\n")
        self.text.insert("end", f"Type: {details.get('Type', 'Unknown')}\n")
        self.text.insert("end", f"Kiosk Type: {details.get('Kiosk Type', 'Unknown')}\n")
        self.text.insert("end", f"Number of Computers: {details.get('Computers', 'Unknown')}\n")
        known_issues = len(details.get("Known Issues", []))
        self.text.insert("end", f"Known Issues: {known_issues} total\n")
        self.text.insert("end", "----------------------------\n")

class ChangePasswordFrame(PurpleFrame):
    """
    Change password using /auth/change-password.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        title = PurpleFrame.label(
            self,
            "Change Password",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=20)

        form_frame = PurpleFrame.subframe(self)
        form_frame.pack(pady=10)

        lbl = {"fg": JH_WHITE_TEXT, "bg": JH_PURPLE, "font": ("Segoe UI", 10)}
        width = 30

        tk.Label(form_frame, text="Username:", **lbl).grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.entry_username = tk.Entry(form_frame, width=width)
        self.entry_username.grid(row=0, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="Email:", **lbl).grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.entry_email = tk.Entry(form_frame, width=width)
        self.entry_email.grid(row=1, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="Current Password:", **lbl).grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.entry_current_pw = tk.Entry(form_frame, show="*", width=width)
        self.entry_current_pw.grid(row=2, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="New Password:", **lbl).grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.entry_new_pw = tk.Entry(form_frame, show="*", width=width)
        self.entry_new_pw.grid(row=3, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="PIN:", **lbl).grid(row=4, column=0, sticky="e", padx=5, pady=4)
        self.entry_pin = tk.Entry(form_frame, show="*", width=width)
        self.entry_pin.grid(row=4, column=1, padx=5, pady=4)

        self.status_label = PurpleFrame.label(self, "", font=("Segoe UI", 10))
        self.status_label.pack(pady=(5, 0))

        btn_frame = PurpleFrame.subframe(self)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Submit",
            width=14,
            command=self.handle_submit,
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            btn_frame,
            text="Back to Utilities",
            width=14,
            command=lambda: self.controller.show_frame("UtilitiesFrame"),
        ).grid(row=0, column=1, padx=8)

        self.bind("<<ShowFrame>>", self.on_show_frame)


    def on_show_frame(self, event=None):
        # Pre-fill username/email from logged in user if available
        self.entry_username.delete(0, "end")
        self.entry_email.delete(0, "end")

        if self.controller.current_username:
            self.entry_username.insert(0, self.controller.current_username)
        if self.controller.current_email:
            self.entry_email.insert(0, self.controller.current_email)

        self.entry_current_pw.delete(0, "end")
        self.entry_new_pw.delete(0, "end")
        self.entry_pin.delete(0, "end")
        self.status_label.config(text="")

    def handle_submit(self):
        username = self.entry_username.get().strip()
        email = self.entry_email.get().strip()
        current_pw = self.entry_current_pw.get()
        new_pw = self.entry_new_pw.get()
        pin = self.entry_pin.get()

        if not all([username, email, current_pw, new_pw, pin]):
            messagebox.showerror("Validation Error", "All fields are required.")
            return

        self.status_label.config(text="Submitting password change...")
        self.update_idletasks()

        success, msg = api_change_password(email, username, current_pw, new_pw, pin)
        self.status_label.config(text=msg)

        if success:
            messagebox.showinfo("Password Changed", msg)
        else:
            messagebox.showerror("Error", msg)

class ChangePINFrame(PurpleFrame):
    """
    Change PIN using /auth/change-pin.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False)

        title = PurpleFrame.label(
            self,
            "Change PIN",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=20)

        form_frame = PurpleFrame.subframe(self)
        form_frame.pack(pady=10)

        lbl = {"fg": JH_WHITE_TEXT, "bg": JH_PURPLE, "font": ("Segoe UI", 10)}
        width = 30

        tk.Label(form_frame, text="Username:", **lbl).grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.entry_username = tk.Entry(form_frame, width=width)
        self.entry_username.grid(row=0, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="Email:", **lbl).grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.entry_email = tk.Entry(form_frame, width=width)
        self.entry_email.grid(row=1, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="Account Password:", **lbl).grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.entry_password = tk.Entry(form_frame, show="*", width=width)
        self.entry_password.grid(row=2, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="Current PIN:", **lbl).grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.entry_current_pin = tk.Entry(form_frame, show="*", width=width)
        self.entry_current_pin.grid(row=3, column=1, padx=5, pady=4)

        tk.Label(form_frame, text="New PIN:", **lbl).grid(row=4, column=0, sticky="e", padx=5, pady=4)
        self.entry_new_pin = tk.Entry(form_frame, show="*", width=width)
        self.entry_new_pin.grid(row=4, column=1, padx=5, pady=4)

        self.status_label = PurpleFrame.label(self, "", font=("Segoe UI", 10))
        self.status_label.pack(pady=(5, 0))

        btn_frame = PurpleFrame.subframe(self)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Submit",
            width=14,
            command=self.handle_submit,
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            btn_frame,
            text="Back to Utilities",
            width=14,
            command=lambda: self.controller.show_frame("UtilitiesFrame"),
        ).grid(row=0, column=1, padx=8)

        self.bind("<<ShowFrame>>", self.on_show_frame)


    def on_show_frame(self, event=None):
        self.entry_username.delete(0, "end")
        self.entry_email.delete(0, "end")

        if self.controller.current_username:
            self.entry_username.insert(0, self.controller.current_username)
        if self.controller.current_email:
            self.entry_email.insert(0, self.controller.current_email)

        self.entry_password.delete(0, "end")
        self.entry_current_pin.delete(0, "end")
        self.entry_new_pin.delete(0, "end")
        self.status_label.config(text="")

    def handle_submit(self):
        username = self.entry_username.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_password.get()
        current_pin = self.entry_current_pin.get()
        new_pin = self.entry_new_pin.get()

        if not all([username, email, password, current_pin, new_pin]):
            messagebox.showerror("Validation Error", "All fields are required.")
            return

        self.status_label.config(text="Submitting PIN change...")
        self.update_idletasks()

        success, msg = api_change_pin(email, username, password, current_pin, new_pin)
        self.status_label.config(text=msg)

        if success:
            messagebox.showinfo("PIN Changed", msg)
        else:
            messagebox.showerror("Error", msg)

# ----------------------------
# REPORT ISSUE FRAME
# ----------------------------

class ReportIssueFrame(PurpleFrame):
    """
    GUI version of issueAdd():
    - Store number
    - Device type
    - Computer number (if applicable)
    - Category
    - Priority
    - Description
    - Replicable? / Global issue info
    - Issue name
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.stores = None  # will be loaded from API
        self.pack_propagate(False)

        title = PurpleFrame.label(self, "Report New Issue", font=("Segoe UI", 20, "bold"))
        title.pack(pady=20)

        self.status_label = PurpleFrame.label(self, "", font=("Segoe UI", 10))
        self.status_label.pack(pady=(0, 10))

        form = PurpleFrame.subframe(self)
        form.pack(pady=5, padx=20, fill="x")

        label_style = {"fg": JH_WHITE_TEXT, "bg": JH_PURPLE, "font": ("Segoe UI", 10)}
        entry_width = 30

        # Row 0: Store number
        tk.Label(form, text="Store number:", **label_style).grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.entry_store_num = tk.Entry(form, width=entry_width)
        self.entry_store_num.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        # Row 1: Device type
        tk.Label(form, text="Device type:", **label_style).grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.entry_device = tk.Entry(form, width=entry_width)
        self.entry_device.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        # Row 2: Computer number
        tk.Label(form, text="Computer number (if computer):", **label_style).grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.entry_comp_num = tk.Entry(form, width=entry_width)
        self.entry_comp_num.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        # Row 3: Category
        tk.Label(form, text="Issue category:", **label_style).grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.entry_category = tk.Entry(form, width=entry_width)
        self.entry_category.insert(0, "Hardware/Software/Network/etc.")
        self.entry_category.grid(row=3, column=1, sticky="w", padx=5, pady=4)

        # Row 4: Priority (1/2/3 like CLI)
        tk.Label(form, text="Priority:", **label_style).grid(row=4, column=0, sticky="e", padx=5, pady=4)
        self.priority_var = tk.StringVar(value="1 - Critical")
        priority_options = ["1 - Critical", "2 - Functional", "3 - Cosmetic"]
        self.priority_menu = tk.OptionMenu(form, self.priority_var, *priority_options)
        self.priority_menu.grid(row=4, column=1, sticky="w", padx=5, pady=4)

        # Row 5: Replicable?
        tk.Label(form, text="Replicable on other systems?:", **label_style).grid(row=5, column=0, sticky="e", padx=5, pady=4)
        self.replicable_var = tk.StringVar(value="No")
        self.replicable_menu = tk.OptionMenu(form, self.replicable_var, "Yes", "No")
        self.replicable_menu.grid(row=5, column=1, sticky="w", padx=5, pady=4)

        # Row 6: Global issue fields
        tk.Label(form, text="Global issue (more than one device)?:", **label_style).grid(row=6, column=0, sticky="e", padx=5, pady=4)
        self.global_issue_var = tk.StringVar(value="No")
        self.global_issue_menu = tk.OptionMenu(form, self.global_issue_var, "Yes", "No")
        self.global_issue_menu.grid(row=6, column=1, sticky="w", padx=5, pady=4)

        tk.Label(form, text="If global, how many devices?:", **label_style).grid(row=7, column=0, sticky="e", padx=5, pady=4)
        self.entry_global_num = tk.Entry(form, width=entry_width)
        self.entry_global_num.grid(row=7, column=1, sticky="w", padx=5, pady=4)

        # Row 8: Issue name
        tk.Label(form, text="Issue name:", **label_style).grid(row=8, column=0, sticky="e", padx=5, pady=4)
        self.entry_issue_name = tk.Entry(form, width=entry_width + 10)
        self.entry_issue_name.grid(row=8, column=1, sticky="w", padx=5, pady=4)

        # Row 9: Description (multi-line)
        PurpleFrame.label(self, "Description:", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        self.text_description = scrolledtext.ScrolledText(self, width=70, height=6, wrap="word")
        self.text_description.pack(padx=20, pady=5, fill="x")

        # Buttons
        btn_frame = PurpleFrame.subframe(self)
        btn_frame.pack(pady=20)

        submit_btn = tk.Button(btn_frame, text="Submit Issue", command=self.handle_submit, width=20)
        submit_btn.grid(row=0, column=0, padx=10)

        back_btn = tk.Button(
            btn_frame,
            text="Back to Main Menu",
            command=lambda: self.controller.show_frame("MainMenuFrame"),
            width=20
        )
        back_btn.grid(row=0, column=1, padx=10)

        self.bind("<<ShowFrame>>", self.on_show_frame)


    def on_show_frame(self, event=None):
        """
        When this frame is shown, ensure stores are loaded (for validation)
        and clear status text.
        """
        self.status_label.config(text="")
        # Optionally load stores here so first submit isn't slow
        if self.stores is None:
            stores, error = api_load_stores()
            if stores is None:
                self.status_label.config(text=error or "Could not load stores list.")
            else:
                self.stores = stores

    def resolve_store_name(self, store_number: str):
        """
        Given a store number string, find the matching store_name
        in the stores dict returned by /stores.
        """
        if not self.stores:
            return None

        for store_name, details in self.stores.items():
            if str(details.get("Store Number")) == str(store_number):
                return store_name
        return None

    def handle_submit(self):
        # Basic required fields
        sNum = self.entry_store_num.get().strip()
        devName = self.entry_device.get().strip()
        compNum = self.entry_comp_num.get().strip()
        category = self.entry_category.get().strip()
        priority_choice = self.priority_var.get()
        replicable_choice = self.replicable_var.get()
        global_issue_choice = self.global_issue_var.get()
        global_num_raw = self.entry_global_num.get().strip()
        issue_name = self.entry_issue_name.get().strip()
        desc = self.text_description.get("1.0", "end").strip()

        # Validation
        if not sNum.isdigit():
            messagebox.showerror("Validation Error", "Store number must be a number.")
            return

        if not devName:
            messagebox.showerror("Validation Error", "Device type is required.")
            return

        if not category or category == "Hardware/Software/Network/etc.":
            messagebox.showerror("Validation Error", "Please enter an issue category.")
            return

        if not issue_name:
            messagebox.showerror("Validation Error", "Please enter an issue name.")
            return

        if not desc:
            messagebox.showerror("Validation Error", "Please enter a description.")
            return

        # Load stores if not already loaded
        if self.stores is None:
            stores, error = api_load_stores()
            if stores is None:
                messagebox.showerror("Error", error or "Could not load stores list.")
                return
            self.stores = stores

        # Resolve store_name from store number
        store_name = self.resolve_store_name(sNum)
        if not store_name:
            messagebox.showerror("Validation Error", "Store number not found in store list.")
            return

        # Priority: keep "1"/"2"/"3" like CLI
        priority = priority_choice.split(" ")[0]

        # Replicable? (Yes/No)
        repro = "Yes" if replicable_choice == "Yes" else "No"

        # Global issue + number
        gIssue = global_issue_choice == "Yes"
        gNum = None
        if gIssue:
            if global_num_raw:
                if not global_num_raw.isdigit():
                    messagebox.showerror("Validation Error", "Global device count must be a whole number.")
                    return
                gNum = int(global_num_raw)

        # Computer number logic
        if "computer" in devName.lower() and not compNum:
            if not messagebox.askyesno(
                "No Computer Number",
                "Device type includes 'computer' but computer number is blank.\n\n"
                "Submit anyway with 'N/A'?"
            ):
                return
            compNum = "N/A"
        elif not compNum:
            compNum = "N/A"

        # Build issue dict in legacy format expected by backend
        new_issue = {
            "Name": issue_name,
            "Issue Name": issue_name,
            "Priority": priority,
            "Store Number": sNum,
            "Computer Number": compNum,
            "Device": devName,
            "Category": category,
            "Description": desc,
            "Narrative": "",
            "Replicable?": repro,
            "Global Issue": gIssue,
            "Global Number": gNum,
            "Status": "Unresolved",
            "Resolution": ""
        }

        self.status_label.config(text="Submitting issue...")
        self.update_idletasks()

        success, msg = api_add_issue(store_name, new_issue)

        if success:
            messagebox.showinfo("Issue Submitted", f"Issue '{issue_name}' added to {store_name}.")
            self.clear_fields()
            self.status_label.config(text="Issue submitted successfully.")
        else:
            messagebox.showerror("Error", msg)
            self.status_label.config(text=msg)

    def clear_fields(self):
        self.entry_store_num.delete(0, "end")
        self.entry_device.delete(0, "end")
        self.entry_comp_num.delete(0, "end")
        self.entry_category.delete(0, "end")
        self.entry_category.insert(0, "Hardware/Software/Network/etc.")
        self.priority_var.set("1 - Critical")
        self.replicable_var.set("No")
        self.global_issue_var.set("No")
        self.entry_global_num.delete(0, "end")
        self.entry_issue_name.delete(0, "end")
        self.text_description.delete("1.0", "end")

# ----------------------------
# EDIT ISSUE FRAME
# ----------------------------

class EditIssueFrame(PurpleFrame):
    """
    Edit Issue screen.

    Flow:
    - User enters either:
        * a store number (digits only), OR
        * search text to look for in issue names
    - Click "Search"
    - Shows "Searching the database..." while scanning
    - If matches found, a dropdown appears with issues
    - User selects an issue and clicks "Load Issue"
    - Fields appear pre-filled and can be edited
    - "Save Changes" writes back via api_update_issue()
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # We'll search directly in the issues table via API
        self.matches = []      # list of row dicts from the DB
        self.match_map = {}    # display_text -> row dict
        self.current_issue_id: int | None = None

        # -------------------------
        # SCROLLABLE AREA SETUP
        # -------------------------
        # Container to hold canvas + scrollbar
        scroll_container = PurpleFrame.subframe(self)
        scroll_container.pack(fill="both", expand=True)

        # Canvas and vertical scrollbar
        self.canvas = tk.Canvas(
            scroll_container,
            bg=JH_PURPLE,
            highlightthickness=0
        )
        vscroll = tk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=vscroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        # Inner frame that actually holds all the widgets
        self.inner_frame = PurpleFrame.subframe(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw"
        )


        # Make the scrollregion match inner_frame size
        def _on_inner_config(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.inner_frame.bind("<Configure>", _on_inner_config)

        # Optional: allow mouse wheel scrolling (Windows)
        def _on_mousewheel(event):
            # On Windows, event.delta is typically ±120 per notch
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # -------------------------
        # BUILD UI INTO inner_frame
        # -------------------------

        # --- Title ---
        title = PurpleFrame.label(
            self.inner_frame,
            "Edit Existing Issue",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=20)

        # --- Status label ---
        self.status_label = PurpleFrame.label(
            self.inner_frame,
            "",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=(0, 10))

        # --- Search area ---
        search_frame = PurpleFrame.subframe(self.inner_frame)
        search_frame.pack(pady=10, padx=20, fill="x")

        PurpleFrame.label(
            search_frame,
            "Enter a store number OR search for issue by name:",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))

        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        search_btn = tk.Button(
            search_frame,
            text="Search",
            width=12,
            command=self.handle_search
        )
        search_btn.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # --- Results / issue selector ---
        # We'll pack this only when we have results
        self.selector_frame = PurpleFrame.subframe(self.inner_frame)
        self.issue_var = tk.StringVar(value="")
        self.issue_menu = None

        # --- Edit form (initially hidden) ---
        self.form_frame = PurpleFrame.subframe(self.inner_frame)
        self.build_form(self.form_frame)
        # NOTE: self.form_frame is NOT packed yet; we do that in load_selected_issue()

        # --- Bottom buttons (back) ---
        bottom_frame = PurpleFrame.subframe(self.inner_frame)
        bottom_frame.pack(pady=15)
        tk.Button(
            bottom_frame,
            text="Back to Main Menu",
            width=18,
            command=lambda: self.controller.show_frame("MainMenuFrame")
        ).pack()

        # When this frame is shown
        self.bind("<<ShowFrame>>", self.on_show_frame)

    # ---------- UI building ----------

    def build_form(self, parent):
        """Create the edit form widgets inside parent."""
        label_style = {"fg": JH_WHITE_TEXT, "bg": JH_PURPLE, "font": ("Segoe UI", 10)}
        entry_width = 30

        form = PurpleFrame.subframe(parent)
        form.pack(pady=5, padx=20, fill="x")

        # Row 0: Store number
        tk.Label(form, text="Store number:", **label_style).grid(
            row=0, column=0, sticky="e", padx=5, pady=3
        )
        self.entry_store_num = tk.Entry(form, width=entry_width)
        self.entry_store_num.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        # Row 1: Device type
        tk.Label(form, text="Device type:", **label_style).grid(
            row=1, column=0, sticky="e", padx=5, pady=3
        )
        self.entry_device = tk.Entry(form, width=entry_width)
        self.entry_device.grid(row=1, column=1, sticky="w", padx=5, pady=3)

        # Row 2: Computer number
        tk.Label(form, text="Computer number:", **label_style).grid(
            row=2, column=0, sticky="e", padx=5, pady=3
        )
        self.entry_comp_num = tk.Entry(form, width=entry_width)
        self.entry_comp_num.grid(row=2, column=1, sticky="w", padx=5, pady=3)

        # Row 3: Category
        tk.Label(form, text="Category:", **label_style).grid(
            row=3, column=0, sticky="e", padx=5, pady=3
        )
        self.entry_category = tk.Entry(form, width=entry_width)
        self.entry_category.grid(row=3, column=1, sticky="w", padx=5, pady=3)

        # Row 4: Priority
        tk.Label(form, text="Priority:", **label_style).grid(
            row=4, column=0, sticky="e", padx=5, pady=3
        )
        self.priority_var = tk.StringVar(value="Choose...")
        priority_options = ["Choose...", "1 - Critical", "2 - Functional", "3 - Cosmetic"]
        self.priority_menu = tk.OptionMenu(form, self.priority_var, *priority_options)
        self.priority_menu.grid(row=4, column=1, sticky="w", padx=5, pady=3)

        # Row 5: Replicable?
        tk.Label(form, text="Replicable on other systems?:", **label_style).grid(
            row=5, column=0, sticky="e", padx=5, pady=3
        )
        self.replicable_var = tk.StringVar(value="No")
        self.replicable_menu = tk.OptionMenu(form, self.replicable_var, "Yes", "No")
        self.replicable_menu.grid(row=5, column=1, sticky="w", padx=5, pady=3)

        # Row 6: Global?
        tk.Label(form, text="Global issue?:", **label_style).grid(
            row=6, column=0, sticky="e", padx=5, pady=3
        )
        self.global_issue_var = tk.StringVar(value="No")
        self.global_issue_menu = tk.OptionMenu(form, self.global_issue_var, "Yes", "No")
        self.global_issue_menu.grid(row=6, column=1, sticky="w", padx=5, pady=3)

        tk.Label(form, text="If global, how many devices?:", **label_style).grid(
            row=7, column=0, sticky="e", padx=5, pady=3
        )
        self.entry_global_num = tk.Entry(form, width=entry_width)
        self.entry_global_num.grid(row=7, column=1, sticky="w", padx=5, pady=3)

        # Row 8: Issue name
        tk.Label(form, text="Issue name:", **label_style).grid(
            row=8, column=0, sticky="e", padx=5, pady=3
        )
        self.entry_issue_name = tk.Entry(form, width=entry_width + 10)
        self.entry_issue_name.grid(row=8, column=1, sticky="w", padx=5, pady=3)

        # Row 9: Status
        tk.Label(form, text="Status:", **label_style).grid(
            row=9, column=0, sticky="e", padx=5, pady=3
        )
        self.status_var = tk.StringVar(value="Unresolved")
        status_options = ["Unresolved", "In Progress", "Resolved", "Closed"]
        self.status_menu = tk.OptionMenu(form, self.status_var, *status_options)
        self.status_menu.grid(row=9, column=1, sticky="w", padx=5, pady=3)

        # Description
        PurpleFrame.label(parent, "Description:", font=("Segoe UI", 10)).pack(
            anchor="w", padx=25
        )
        self.text_description = scrolledtext.ScrolledText(
            parent, width=70, height=4, wrap="word"
        )
        self.text_description.pack(padx=25, pady=3, fill="x")

        #narrative
        PurpleFrame.label(parent, "Narrative:", font=("Segoe UI", 10)).pack(
            anchor="w", padx=25
        )
        self.text_narrative = scrolledtext.ScrolledText(
            parent, width=70, height=4, wrap="word"
        )
        self.text_narrative.pack(padx=25, pady=3, fill="x")

        # Resolution
        PurpleFrame.label(parent, "Resolution (if any):", font=("Segoe UI", 10)).pack(
            anchor="w", padx=25
        )
        self.text_resolution = scrolledtext.ScrolledText(
            parent, width=70, height=3, wrap="word"
        )
        self.text_resolution.pack(padx=25, pady=3, fill="x")

        # Save/Cancel buttons
        btn_frame = PurpleFrame.subframe(parent)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame,
            text="Save Changes",
            width=18,
            command=self.handle_save
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel Changes",
            width=18,
            command=self.clear_form
        ).grid(row=0, column=1, padx=10)

    # ---------- Frame lifecycle ----------

    def on_show_frame(self, event=None):
        self.status_label.config(text="")
        self.search_entry.delete(0, "end")
        self.matches = []
        self.match_map = {}
        self.current_issue_id = None

        # Hide selector + form until needed
        self.selector_frame.pack_forget()
        self.form_frame.pack_forget()

        # Reset scroll to top when we enter this screen
        self.canvas.yview_moveto(0.0)

    # ---------- Search logic ----------

    def handle_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning(
                "Input Required",
                "Please enter a store number or search text."
            )
            return

        self.status_label.config(text="Searching the database...")
        self.update_idletasks()

        self.matches = []
        self.match_map.clear()

        # Decide: store number vs issue name search
        if query.isdigit():
            ok, rows, error = api_search_issues(store_number=int(query), name=None)
        else:
            ok, rows, error = api_search_issues(store_number=None, name=query)

        if not ok:
            self.selector_frame.pack_forget()
            self.form_frame.pack_forget()
            self.status_label.config(text=error or "Search failed.")
            messagebox.showerror("Search Error", error or "Search failed.")
            return

        if not rows:
            self.selector_frame.pack_forget()
            self.form_frame.pack_forget()
            self.status_label.config(text="No matching issues found.")
            return

        # Build matches + mapping
        self.matches = rows
        self.match_map = {}

        for row in rows:
            store_num = row.get("store_number", "Unknown")
            name = row.get("issue_name") or row.get("issue") or "Unnamed Issue"
            display = f"Store {store_num} – {name}"
            self.match_map[display] = row  # if duplicates, last wins

        self.build_selector_ui()
        self.status_label.config(
            text=f"Found {len(self.matches)} matching issue(s)."
        )

    def build_selector_ui(self):
        # Clear old selector if any
        for child in self.selector_frame.winfo_children():
            child.destroy()

        PurpleFrame.label(
            self.selector_frame,
            "Select an issue to edit:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=25, pady=(5, 2))

        # Build dropdown
        options = list(self.match_map.keys())
        options.sort()

        self.issue_var.set(options[0])
        if self.issue_menu is not None:
            self.issue_menu.destroy()

        self.issue_menu = tk.OptionMenu(self.selector_frame, self.issue_var, *options)
        self.issue_menu.pack(anchor="w", padx=25, pady=3)

        tk.Button(
            self.selector_frame,
            text="Load Issue",
            width=15,
            command=self.load_selected_issue
        ).pack(anchor="w", padx=25, pady=5)

        self.selector_frame.pack(pady=10, fill="x")

    # ---------- Load + show issue ----------

    def load_selected_issue(self):
        key = self.issue_var.get()
        if key not in self.match_map:
            messagebox.showerror("Error", "Please select an issue.")
            return

        row = self.match_map[key]
        self.current_issue_id = row.get("id")

        # Populate fields from DB row
        self.entry_store_num.delete(0, "end")
        self.entry_store_num.insert(0, str(row.get("store_number") or ""))

        self.entry_device.delete(0, "end")
        self.entry_device.insert(0, row.get("device_type") or "")

        self.entry_comp_num.delete(0, "end")
        self.entry_comp_num.insert(0, row.get("computer_number") or "")

        self.entry_category.delete(0, "end")
        self.entry_category.insert(0, row.get("category") or "")

        # Priority (stored as text like "1", "2", "3")
        pr = str(row.get("priority") or "1")
        if pr == "1":
            self.priority_var.set("1 - Critical")
        elif pr == "2":
            self.priority_var.set("2 - Functional")
        elif pr == "3":
            self.priority_var.set("3 - Cosmetic")
        else:
            self.priority_var.set("1 - Critical")

        # Replicable
        repro = row.get("replicable") or ""
        self.replicable_var.set(
            "Yes" if str(repro).strip().lower().startswith(("y", "t", "1")) else "No"
        )

        # Global issue
        g_issue = row.get("global_issue")
        self.global_issue_var.set("Yes" if g_issue else "No")

        self.entry_global_num.delete(0, "end")
        g_num = row.get("global_num")
        if g_num is not None:
            self.entry_global_num.insert(0, str(g_num))

        # Issue name
        self.entry_issue_name.delete(0, "end")
        self.entry_issue_name.insert(0, row.get("issue_name") or "")

        # Status
        self.status_var.set(row.get("status") or "Unresolved")

        # Description
        self.text_description.delete("1.0", "end")
        self.text_description.insert("1.0", row.get("description") or "")

        # Narrative
        self.text_narrative.delete("1.0", "end")
        self.text_narrative.insert("1.0", row.get("narrative") or "")

        # Resolution
        self.text_resolution.delete("1.0", "end")
        self.text_resolution.insert("1.0", row.get("resolution") or "")

        # Show the form (scrollable)
        self.form_frame.pack(pady=10, fill="both", expand=True)

    # ---------- Saving ----------

    def handle_save(self):
        if self.current_issue_id is None:
            messagebox.showerror("Error", "No issue is currently loaded.")
            return

        sNum = self.entry_store_num.get().strip()
        devName = self.entry_device.get().strip()
        compNum = self.entry_comp_num.get().strip()
        category = self.entry_category.get().strip()
        priority_choice = self.priority_var.get()
        replicable_choice = self.replicable_var.get()
        global_issue_choice = self.global_issue_var.get()
        global_num_raw = self.entry_global_num.get().strip()
        issue_name = self.entry_issue_name.get().strip()
        status_choice = self.status_var.get()
        desc = self.text_description.get("1.0", "end").strip()
        narrative = self.text_narrative.get("1.0", "end").strip()
        resolution_text = self.text_resolution.get("1.0", "end").strip()

        # Basic validation
        if not sNum.isdigit():
            messagebox.showerror("Validation Error", "Store number must be a number.")
            return
        if not issue_name:
            messagebox.showerror("Validation Error", "Issue name is required.")
            return
        if not devName:
            messagebox.showerror("Validation Error", "Device type is required.")
            return
        if not category:
            messagebox.showerror("Validation Error", "Category is required.")
            return

        if not desc:
            if not messagebox.askyesno(
                    "Empty Description",
                    "Description is empty. Save changes anyway?"
            ):
                return

        if not narrative:
            if not messagebox.askyesno(
                    "Empty Narrative",
                    "Narrative is empty. Save changes anyway?"
            ):
                return

        # Priority
        priority = priority_choice.split(" ")[0]

        # Replicable
        repro = "Yes" if replicable_choice == "Yes" else "No"

        # Global issue
        gIssue = global_issue_choice == "Yes"
        gNum = None
        if gIssue and global_num_raw:
            if not global_num_raw.isdigit():
                messagebox.showerror(
                    "Validation Error",
                    "Global device count must be a whole number."
                )
                return
            gNum = int(global_num_raw)

        # Computer number
        if "computer" in devName.lower() and not compNum:
            if not messagebox.askyesno(
                "No Computer Number",
                "Device type includes 'computer' but computer number is blank.\n\n"
                "Save anyway with 'N/A'?"
            ):
                return
            compNum = "N/A"
        elif not compNum:
            compNum = "N/A"

        updated_issue = {
            "Name": issue_name,
            "Issue Name": issue_name,
            "Priority": priority,
            "Store Number": sNum,
            "Computer Number": compNum,
            "Device": devName,
            "Category": category,
            "Description": desc,
            "Narrative": narrative,
            "Replicable?": repro,
            "Global Issue": gIssue,
            "Global Number": gNum,
            "Status": status_choice,
            "Resolution": resolution_text,
        }

        success, msg = api_update_issue(self.current_issue_id, updated_issue)

        success, msg = api_update_issue(self.current_issue_id, updated_issue)

        if success:
            # Update cached match entry so re-loading shows new values
            if self.current_issue_id is not None:
                for k, row in self.match_map.items():
                    if row.get("id") == self.current_issue_id:
                        # Keep store_name as-is if we don't edit it here
                        row["store_number"] = int(sNum)
                        row["device_type"] = devName
                        row["computer_number"] = compNum
                        row["category"] = category
                        row["priority"] = priority  # "1", "2", or "3"
                        row["description"] = desc
                        row["narrative"] = narrative
                        # store as a simple truthy flag
                        row["replicable"] = (repro == "Yes")
                        row["global_issue"] = gIssue
                        row["global_num"] = gNum
                        row["status"] = status_choice
                        row["resolution"] = resolution_text
                        break

            messagebox.showinfo("Issue Updated", msg)
            self.status_label.config(text=msg)
        else:
            messagebox.showerror("Update Error", msg)
            self.status_label.config(text=msg)

    def clear_form(self):
        """Reset form fields but keep search results."""
        self.entry_store_num.delete(0, "end")
        self.entry_device.delete(0, "end")
        self.entry_comp_num.delete(0, "end")
        self.entry_category.delete(0, "end")
        self.priority_var.set("1 - Critical")
        self.replicable_var.set("No")
        self.global_issue_var.set("No")
        self.entry_global_num.delete(0, "end")
        self.entry_issue_name.delete(0, "end")
        self.status_var.set("Unresolved")
        self.text_description.delete("1.0", "end")
        self.text_narrative.delete("1.0", "end")
        self.text_resolution.delete("1.0", "end")

# ----------------------------
# VIEW ONE ISSUE FRAME
# ----------------------------

class ViewOneStoreFrame(PurpleFrame):
    """
    View issues for a single store by store number or store name.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = PurpleFrame.label(
            self,
            "View Issues – One Store",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=20)

        self.status_label = PurpleFrame.label(
            self,
            "",
            font=("Segoe UI", 10),
        )
        self.status_label.pack(pady=(0, 10))

        # --- Search area ---
        search_frame = PurpleFrame.subframe(self)
        search_frame.pack(pady=10, padx=20, fill="x")

        PurpleFrame.label(
            search_frame,
            "Enter a store number OR exact store name:",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))

        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tk.Button(
            search_frame,
            text="Load Issues",
            width=15,
            command=self.handle_search,
        ).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # --- Results area ---
        self.text = scrolledtext.ScrolledText(
            self,
            width=80,
            height=20,
            wrap="word",
            bg=JH_PURPLE,
            fg=JH_WHITE_TEXT,
        )
        self.text.pack(padx=20, pady=10, fill="both", expand=True)

        # Header lines (issue number + name) will be yellow & bold
        self.text.tag_configure(
            "issue_header",
            foreground="yellow",
            font=("Segoe UI", 10, "bold"),
        )

        # Back button
        bottom_frame = PurpleFrame.subframe(self)
        bottom_frame.pack(pady=10)
        tk.Button(
            bottom_frame,
            text="Back to Main Menu",
            width=18,
            command=lambda: self.controller.show_frame("MainMenuFrame"),
        ).pack()

        self.bind("<<ShowFrame>>", self.on_show_frame)


    def on_show_frame(self, event=None):
        self.status_label.config(text="")
        self.search_entry.delete(0, "end")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def handle_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning(
                "Input Required",
                "Please enter a store number or store name.",
            )
            return

        # Decide if this is a store number or name
        store_number = None
        store_name = None
        if query.isdigit():
            store_number = int(query)
        else:
            store_name = query

        ok, rows, error = api_get_issues_by_store(
            store_number=store_number,
            store_name=store_name,
        )

        if not ok:
            self.status_label.config(text=error or "Failed to load issues.")
            messagebox.showerror(
                "Error",
                error or "Failed to load issues for that store.",
            )
            return

        if not rows:
            self.status_label.config(text="No issues found for that store.")
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("end", "No issues found for that store.\n")
            self.text.configure(state="disabled")
            return

        self.render_issues(rows)

    def render_issues(self, rows: list[dict]):
        first = rows[0]
        store_name = first.get("store_name") or "Unknown Store"
        store_number = first.get("store_number") or "Unknown"

        header = f"Viewing Issues for {store_name} (Store {store_number})\n\n"

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", header)

        for idx, row in enumerate(rows, start=1):
            issue_name = row.get("issue_name") or "Unnamed Issue"
            status = row.get("status") or "Unresolved"

            # Header line: number + issue name + [status] in yellow
            header_line = f"{idx}. {issue_name} [{status}]\n"
            self.text.insert("end", header_line, ("issue_header",))

            # Device
            device = row.get("device_type") or ""
            if device:
                self.text.insert("end", f"Device: {device}\n")

            # Category
            category = row.get("category") or ""
            if category:
                self.text.insert("end", f"Category: {category}\n")

            # Computer number (only if present and not "N/A")
            comp = row.get("computer_number")
            if comp and str(comp).strip().upper() != "N/A":
                self.text.insert("end", f"Computer: {comp}\n")

            # Priority conversion
            priority_raw = row.get("priority")
            pretty_priority = "Unknown"
            if priority_raw is not None:
                val = str(priority_raw).strip()
                if val == "1":
                    pretty_priority = "Critical"
                elif val == "2":
                    pretty_priority = "Functional"
                elif val == "3":
                    pretty_priority = "Cosmetic"
                else:
                    pretty_priority = val
            self.text.insert("end", f"Priority: {pretty_priority}\n")

            # Global issue info
            g_issue = row.get("global_issue")
            if g_issue is not None:
                self.text.insert(
                    "end", f"Global issue: {'Yes' if g_issue else 'No'}\n"
                )
            g_num = row.get("global_num")
            if g_num is not None:
                self.text.insert("end", f"Devices affected: {g_num}\n")

            # Description
            desc = row.get("description") or ""
            if desc:
                self.text.insert("end", f"Description:\n{desc}\n")

            # Narrative
            narrative = row.get("narrative") or ""
            if narrative:
                self.text.insert("end", f"Narrative:\n{narrative}\n")

            # Resolution
            resolution = row.get("resolution") or ""
            if resolution:
                self.text.insert("end", f"Resolution:\n{resolution}\n")

            # Separator
            self.text.insert("end", "\n----    ----    ----    ----    \n\n")

        self.text.configure(state="disabled")
        self.status_label.config(text=f"Showing {len(rows)} issue(s).")

# ----------------------------
# VIEW ALL ISSUE FRAME
# ----------------------------

class ViewAllIssuesFrame(PurpleFrame):
    """
    View all issues for all stores, grouped by store.

    NOTE:
    - Uses api_load_stores() to get store metadata.
    - Uses api_get_issues_by_store() to get issues per store.
    - Calls update_idletasks() inside the loop so the UI doesn't appear frozen.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = PurpleFrame.label(
            self,
            "View All Issues",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=20)

        self.status_label = PurpleFrame.label(
            self,
            "",
            font=("Segoe UI", 10),
        )
        self.status_label.pack(pady=(0, 10))

        # Button to refresh/load all
        top_btn_frame = PurpleFrame.subframe(self)
        top_btn_frame.pack(pady=5)
        tk.Button(
            top_btn_frame,
            text="Load / Refresh All Issues",
            width=22,
            command=self.handle_refresh,
        ).pack()

        # Text area
        self.text = scrolledtext.ScrolledText(
            self,
            width=80,
            height=22,
            wrap="word",
            bg=JH_PURPLE,
            fg=JH_WHITE_TEXT,
        )
        self.text.pack(padx=20, pady=10, fill="both", expand=True)

        # Tag for issue header lines
        self.text.tag_configure(
            "issue_header",
            foreground="yellow",
            font=("Segoe UI", 10, "bold"),
        )

        # Tag for store headers (bold white)
        self.text.tag_configure(
            "store_header",
            font=("Segoe UI", 11, "bold"),
        )

        # Back button
        bottom_frame = PurpleFrame.subframe(self)
        bottom_frame.pack(pady=10)
        tk.Button(
            bottom_frame,
            text="Back to Main Menu",
            width=18,
            command=lambda: self.controller.show_frame("MainMenuFrame"),
        ).pack()

        self.bind("<<ShowFrame>>", self.on_show_frame)


    def on_show_frame(self, event=None):
        # Just clear the text / status when entering.
        # User explicitly clicks "Load / Refresh All Issues" to start the heavy work.
        self.status_label.config(text="")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def handle_refresh(self):
        # Step 1: load stores
        self.status_label.config(text="Loading stores from server...")
        self.update_idletasks()

        stores, error = api_load_stores()
        if stores is None:
            self.status_label.config(text=error or "Failed to load stores.")
            messagebox.showerror(
                "Error",
                error or "Failed to load stores metadata.",
            )
            return

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", "Loading issues for all stores...\n\n")
        self.update_idletasks()

        total_issues = 0
        store_count = 0

        # Step 2: loop through stores and fetch issues for each
        # Sort for consistent order
        for sName in sorted(stores.keys()):
            details = stores[sName]
            sNum = details.get("Store Number")

            # Skip stores without a usable store number
            if sNum is None:
                continue

            store_count += 1
            self.status_label.config(
                text=f"Loading issues for {sName} (Store {sNum})..."
            )
            self.update_idletasks()

            ok2, rows, err2 = api_get_issues_by_store(
                store_number=sNum,
                store_name=None,
            )
            if not ok2:
                # If one store fails, log it and keep going
                self.text.insert(
                    "end",
                    f"{sName} (Store {sNum}) – error loading issues: {err2}\n\n",
                )
                self.update_idletasks()
                continue

            if not rows:
                # No issues for this store – skip printing anything
                continue

            total_issues += len(rows)

            # Store header
            self.text.insert(
                "end",
                f"{sName} (Store {sNum})\n",
                ("store_header",),
            )
            self.text.insert("end", "-" * 31 + "\n")

            # Issues under this store
            for idx, row in enumerate(rows, start=1):
                issue_name = row.get("issue_name") or "Unnamed Issue"
                status = row.get("status") or "Unresolved"

                header_line = f"{idx}. {issue_name} [{status}]\n"
                self.text.insert("end", header_line, ("issue_header",))

                device = row.get("device_type") or ""
                if device:
                    self.text.insert("end", f"Device: {device}\n")

                category = row.get("category") or ""
                if category:
                    self.text.insert("end", f"Category: {category}\n")

                comp = row.get("computer_number")
                if comp and str(comp).strip().upper() != "N/A":
                    self.text.insert("end", f"Computer: {comp}\n")

                # Priority conversion
                priority_raw = row.get("priority")
                pretty_priority = "Unknown"
                if priority_raw is not None:
                    val = str(priority_raw).strip()
                    if val == "1":
                        pretty_priority = "Critical"
                    elif val == "2":
                        pretty_priority = "Functional"
                    elif val == "3":
                        pretty_priority = "Cosmetic"
                    else:
                        pretty_priority = val
                self.text.insert("end", f"Priority: {pretty_priority}\n")

                # Global issue
                g_issue = row.get("global_issue")
                if g_issue is not None:
                    self.text.insert(
                        "end", f"Global issue: {'Yes' if g_issue else 'No'}\n"
                    )
                g_num = row.get("global_num")
                if g_num is not None:
                    self.text.insert("end", f"Devices affected: {g_num}\n")

                # Description
                desc = row.get("description") or ""
                if desc:
                    self.text.insert("end", f"Description:\n{desc}\n")

                # Narrative
                narrative = row.get("narrative") or ""
                if narrative:
                    self.text.insert("end", f"Narrative:\n{narrative}\n")

                # Resolution
                resolution = row.get("resolution") or ""
                if resolution:
                    self.text.insert("end", f"Resolution:\n{resolution}\n")

                # Per-issue separator
                self.text.insert("end", "\n----    ----    ----    ----    \n\n")

            # Blank line between stores
            self.text.insert("end", "\n")
            self.update_idletasks()

        if total_issues == 0:
            self.text.insert("end", "No issues found for any store.\n")

        self.text.configure(state="disabled")
        self.status_label.config(
            text=f"Loaded {total_issues} issue(s) across {store_count} store(s)."
        )

# ----------------------------
# ROOT APP
# ----------------------------

class JHApp(tk.Tk):
    """
    Root Tkinter app using a 'frame stack' pattern:
    - LoginFrame
    - MainMenuFrame
    - ReportIssueFrame
    """

    def __init__(self):
        super().__init__()

        self.configure(bg=JH_PURPLE)

        self.title("JH Reports – GUI")
        self.geometry("700x550")
        self.resizable(True, True)

        # Logged-in user info
        self.current_username = None
        self.current_email = None
        self.is_admin = False

        container = tk.Frame(self, bg=JH_PURPLE)
        container.pack(fill="both", expand=True)

        # Make frames resize with window
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (LoginFrame,
                  MainMenuFrame,
                  ReportIssueFrame,
                  EditIssueFrame,
                  ViewOneStoreFrame,
                  ViewAllIssuesFrame,
                  UtilitiesFrame,
                  AdminToolsFrame,
                  StoreSearchFrame,
                  ChangePINFrame,
                  ChangePasswordFrame ):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

        self.current_frame_name = None
        self.show_frame("LoginFrame")

        # Global Enter-key handler for QOL
        self.bind_all("<Return>", self.on_enter_key)

    def show_frame(self, name: str):
        """Raise a frame by its class name and fire <<ShowFrame>>."""
        frame = self.frames.get(name)
        if frame:
            # remember which frame is active
            self.current_frame_name = name
            frame.event_generate("<<ShowFrame>>")
            frame.tkraise()

    def on_enter_key(self, event=None):
        """
        Global handler for the Enter key.

        - On LoginFrame: trigger login
        - On ReportIssueFrame: submit new issue
        - On EditIssueFrame:
            * if no issue loaded yet -> search
            * if issue is loaded -> save changes
        - Ignore Enter if focus is inside a multi-line Text/ScrolledText widget
        """
        # Don't hijack Enter when typing in multi-line text boxes
        if isinstance(getattr(event, "widget", None), tk.Text):
            return

        frame = self.frames.get(getattr(self, "current_frame_name", None))
        if frame is None:
            return

        # Login screen
        if isinstance(frame, LoginFrame):
            frame.handle_login()
            return

        # New issue screen
        if isinstance(frame, ReportIssueFrame):
            frame.handle_submit()
            return

        # Edit issue screen
        if isinstance(frame, EditIssueFrame):
            # If no issue loaded yet, Enter should act like "Search"
            if getattr(frame, "current_issue_id", None) is None:
                frame.handle_search()
            else:
                frame.handle_save()
            return

    def set_user(self, username: str | None, email: str | None = None):
        self.current_username = username
        self.current_email = email
        self.is_admin = is_trusted_admin(email) if email else False


if __name__ == "__main__":
    app = JHApp()
    app.mainloop()
