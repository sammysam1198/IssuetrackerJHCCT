# JHstore_mobile.py

import json
import os
import requests

stores_cache = None

class c:
    RESET = "\033[0m"

    @staticmethod
    def rgb(r, g, b, text):
        return f"\033[38;2;{r};{g};{b}m{text}{c.RESET}"

    @staticmethod
    def bg(r, g, b, text):
        return f"\033[48;2;{r};{g};{b}m{text}{c.RESET}"

    # Theme colors (keep for status messages)
    @staticmethod
    def yellow(text):
        return c.rgb(255, 237, 13, text)

    @staticmethod
    def blue_bg(text):
        # Not used in mobile version; kept for compatibility if needed
        return c.bg(47, 74, 119, text)

    @staticmethod
    def red(text):
        return c.rgb(255, 0, 0, text)

    @staticmethod
    def green(text):
        return c.rgb(0, 255, 0, text)


API_BASE = "https://api-server-jh.onrender.com"  # Render URL

# -----------------------------------
# API + STORE HELPERS
# -----------------------------------

def displayIssues(store_name: str, store_number, issues: list):
    """Pretty-print issues for a store using DB column names."""
    print(f"\n{store_name} {store_number}")
    print("Known Issues:")

    if not issues:
        print(c.yellow("No issues for this store!"))
        return

    for idx, issue in enumerate(issues, start=1):
        issue_name = issue.get("issue_name") or "Unnamed Issue"
        status = issue.get("status") or "Unresolved"
        desc = issue.get("description") or "No description provided"
        res = issue.get("resolution") or "None Provided"
        device_type = issue.get("device_type") or "N/A"
        category = issue.get("category") or "N/A"
        computer = issue.get("computer_number") or "N/A"
        priority = issue.get("priority") or "N/A"

        print(f"\n{idx}. {issue_name} [{status}]")
        print(f"   Device: {device_type}")
        print(f"   Category: {category}")
        print(f"   Computer: {computer}")
        print(f"   Priority: {priority}")

        if status.lower() == "resolved":
            print(f"   Resolution: {res}")
        else:
            print(f"   Description: {desc}")

    print(f"\nnumber of issues: {len(issues)}")


def displaySearchResults(issues: list):
    """
    Pretty-print results of a search across possibly multiple stores.
    """
    if not issues:
        print(c.yellow("\nNo issues matched your search criteria."))
        return

    print("\n***** SEARCH RESULTS *****")

    for idx, issue in enumerate(issues, start=1):
        store_name = issue.get("store_name", "Unknown Store")
        store_number = issue.get("store_number", "N/A")
        issue_name = issue.get("issue_name", "Unnamed Issue")
        status = issue.get("status", "Unresolved")
        priority = issue.get("priority", "N/A")
        device_type = issue.get("device_type", "N/A")
        category = issue.get("category", "N/A")
        computer_number = issue.get("computer_number", "N/A")
        desc = issue.get("description", "No description provided")
        res = issue.get("resolution", "No resolution provided")

        print(f"\n{idx}. {issue_name} [{status}]")
        print(f"   Store: {store_name} ({store_number})")
        print(f"   Device: {device_type}")
        print(f"   Category: {category}")
        print(f"   Computer: {computer_number}")
        print(f"   Priority: {priority}")
        print(f"   Description: {desc}")
        print(f"   Resolution: {res}")

    print(f"\nTotal matches: {len(issues)}")


def apiLoad():
    """Load store metadata from the API (from Stores.json on the server)."""
    print(c.yellow("Connecting to server..."))

    try:
        response = requests.get(f"{API_BASE}/stores", timeout=60)
        response.raise_for_status()
        stores = response.json()
        print("\n" + c.green("Successfully loaded stores from API"))
        return stores
    except requests.RequestException as e:
        print("\n" + c.red(f"Error loading store list from server: {e}"))
        return None


def apiSearchIssues(mode: int, term: str):
    """
    Call GET /issues/search with the appropriate parameter based on mode:
      1 = store_number
      2 = category
      3 = status
      4 = device
      5 = name (issue name)
    Returns a list of matching issues (DB rows) or [] on error.
    """
    params = {}

    if mode == 1:
        params["store_number"] = term
    elif mode == 2:
        params["category"] = term
    elif mode == 3:
        params["status"] = term
    elif mode == 4:
        params["device"] = term
    elif mode == 5:
        params["name"] = term
    else:
        print(c.red("Invalid search mode."))
        return []

    try:
        resp = requests.get(f"{API_BASE}/issues/search", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(c.red(f"Error searching issues on server: {e}"))
        return []


def getIssuesForStore(store_number=None, store_name=None):
    """
    Call GET /issues/by-store with either ?store_number= or ?store_name=.
    Returns a list of issue rows (dicts) from the DB, or [] on error.
    """
    params = {}
    if store_number is not None:
        params["store_number"] = str(store_number)
    elif store_name is not None:
        params["store_name"] = store_name
    else:
        print(c.red("Must provide store_number or store_name to get issues."))
        return []

    try:
        resp = requests.get(f"{API_BASE}/issues/by-store", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(c.red(f"Error fetching issues from server: {e}"))
        return []


def get_stores():
    """Cached loader for store metadata."""
    global stores_cache
    if stores_cache is None:
        stores_cache = apiLoad()
    return stores_cache


def build_legacy_issue_from_db(store_name: str, row: dict) -> dict:
    """
    Convert a DB row into the legacy-style dict used for /issues/update.
    """
    return {
        "Store Name": store_name,
        "Store Number": row.get("store_number"),
        "Name": row.get("issue_name"),
        "Issue Name": row.get("issue_name"),  # keep both keys for safety
        "Priority": row.get("priority"),
        "Computer Number": row.get("computer_number"),
        "Device": row.get("device_type"),     # Device
        "Category": row.get("category"),      # Category
        "Description": row.get("description"),
        "Narrative": row.get("narrative") or "",
        "Replicable?": row.get("replicable"),
        "Status": row.get("status"),
        "Resolution": row.get("resolution") or "",
    }


def apiUpdate(issue_id: int, updated_issue: dict) -> bool:
    """
    Send the edited issue back to the API via POST /issues/update.
    Expects:
      issue_id: DB primary key (issues.id)
      updated_issue: legacy-style dict (Issue Name, Status, etc.)
    """
    payload = {
        "issue_id": issue_id,
        "updated_issue": updated_issue,
    }

    try:
        resp = requests.post(f"{API_BASE}/issues/update", json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(c.red(f"Error updating issue on server: {e}"))
        return False


def apiDelete(issue_id: int) -> bool:
    """
    Delete an issue on the server via POST /issues/delete.
    """
    payload = {"issue_id": issue_id}
    try:
        resp = requests.post(f"{API_BASE}/issues/delete", json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(c.red(f"Error deleting issue on server: {e}"))
        return False


# -----------------------------------
# STORE SEARCH / SELECTION
# -----------------------------------

def issueStoreSearch():
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return None

    while True:
        query = input("\nEnter store number or part of store name (or type 'exit' to cancel): ").strip()

        if not query:
            print(c.red("Please enter something."))
            continue

        if query.lower() == "exit":
            return None

        # --- SEARCH BY STORE NUMBER ---
        if query.isdigit():
            sNum_int = int(query)
            for sName, details in stores.items():
                if details.get("Store Number") == sNum_int:
                    return sName
            print(c.red("No store found with that number."))
            continue

        # --- SEARCH BY STORE NAME ---
        matches = [
            (sName, details)
            for sName, details in stores.items()
            if query.lower() in sName.lower()
        ]

        if not matches:
            print(c.red("No stores found matching that name."))
            continue

        # If only one match, just use it
        if len(matches) == 1:
            return matches[0][0]

        # Disambiguate Store Front vs Walmart if both are present
        types_present = {details.get("Type", "").lower() for _, details in matches}
        filtered = matches

        if "store front" in types_present and "walmart" in types_present:
            while True:
                tchoice = input("Is this a Store front or a Walmart? (SF/WM): ").strip().lower()
                if tchoice == "sf":
                    target_type = "store front"
                    break
                elif tchoice == "wm":
                    target_type = "walmart"
                    break
                else:
                    print(c.red("Please enter SF or WM."))
            filtered = [
                (name, details)
                for name, details in matches
                if details.get("Type", "").lower() == target_type
            ]

        # If still more than one, let user pick from a list
        if len(filtered) > 1:
            print("\nMultiple stores found:")
            for idx, (name, details) in enumerate(filtered, start=1):
                print(
                    f"{idx}. {name} "
                    f"(Type: {details.get('Type', 'Unknown')}, "
                    f"Store Number: {details.get('Store Number', 'Unknown')})"
                )

            while True:
                sel = input("Select a store by number: ").strip()
                if sel.isdigit():
                    sel_int = int(sel)
                    if 1 <= sel_int <= len(filtered):
                        return filtered[sel_int - 1][0]
                print(c.red("Invalid selection. Please try again."))
        else:
            # Exactly one after filtering
            return filtered[0][0]


def issueSelectStore(matches):
    """
    Given a list of (store_name, details) matches,
    choose the correct one based on Type (Walmart vs Store Front).
    """
    # Only one match? Just return it.
    if len(matches) == 1:
        return matches[0]

    # What types do we have?
    types_present = {details.get("Type", "").lower() for _, details in matches}

    # If we have both Store Front and Walmart, ask.
    if "store front" in types_present and "walmart" in types_present:
        while True:
            choice = input("Is this a Store front or a Walmart? (SF/WM): ").strip().lower()
            if choice == "sf":
                target_type = "store front"
                break
            elif choice == "wm":
                target_type = "walmart"
                break
            else:
                print(c.red("Invalid choice. Please enter SF or WM."))

        for name, details in matches:
            if details.get("Type", "").lower() == target_type:
                return name, details

    # If types are weird or only one type exists, fall back to index selection.
    print("\n" + c.yellow("Multiple stores found:"))
    for idx, (name, details) in enumerate(matches, start=1):
        print(
            f"{idx}. {name} "
            f"(Type: {details.get('Type', 'Unknown')}, "
            f"Store Number: {details.get('Store Number', 'Unknown')})"
        )

    while True:
        selection = input("Select a store by number: ").strip()
        if selection.isdigit():
            selection_int = int(selection)
            if 1 <= selection_int <= len(matches):
                return matches[selection_int - 1]
        print(c.red("Invalid selection. Please try again."))


def select_issue_for_store(store_name: str, store_number: int):
    """
    Fetch issues from the DB for a store, let the user pick one.
    Returns the chosen DB row (with 'id', 'issue_name', etc.) or None.
    """
    if store_number is not None:
        issues = getIssuesForStore(store_number=store_number)
    else:
        issues = getIssuesForStore(store_name=store_name)

    if not issues:
        print(c.yellow(f"\nNo issues found for {store_name}."))
        return None

    print(f"\nIssues for {store_name} (Store {store_number}):")
    for idx, issue in enumerate(issues, start=1):
        issue_name = issue.get("issue_name") or "Unnamed Issue"
        status = issue.get("status") or "Unresolved"
        comp = issue.get("computer_number") or "N/A"
        dev = issue.get("device_type") or "N/A"
        cat = issue.get("category") or "N/A"
        print(f"{idx}. {issue_name} [{status}] (Device: {dev}, Category: {cat}, Computer: {comp})")

    while True:
        choice = input("\nSelect an issue number: ").strip()
        if choice.isdigit():
            issue_index = int(choice)
            if 1 <= issue_index <= len(issues):
                return issues[issue_index - 1]
        print(c.red("Invalid selection. Please enter a valid issue number."))


# -----------------------------------
# ISSUE CREATION
# -----------------------------------

def issueAdd():
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    # Collect valid store numbers from store metadata
    valid_store_numbers = {details["Store Number"] for details in stores.values()}

    # Store number input + validation
    while True:
        sNum = input("\nStore number: ")

        try:
            sNum_int = int(sNum)
        except ValueError:
            print("\n" + c.red("Invalid input! Store number must be a number."))
            continue

        if sNum_int not in valid_store_numbers:
            print("\n" + c.red("Store number not found! Please enter a valid number."))
            continue

        break

    devName = input(
        "\nWhat type of device is experiencing the issue? (e.g., Phone, Computer etc.): "
    ).strip()

    if "computer" in devName.lower():
        compNum = input("\nComputer experiencing the issue: ")
    else:
        compNum = "N/A"

    cat = input("\nIssue Category (Hardware/Software/Network/etc.): ")
    priority = input("\n1. Critical\n2. Functional\n3. Cosmetic:\n\nPriority: ")
    desc = input("\nDescribe the issue: ")
    repro = input("\nHas this issue been reproduced on any other systems (Yes/No)?: ")
    iName = input("\nGive this issue a name: ")

    # Resolve sName from store number
    sName = None
    for store, details in stores.items():
        if str(details["Store Number"]) == sNum:
            sName = store
            break

    if not sName:
        print("\n" + c.red("Store number not found! Please try again"))
        return

    # Define new issue in legacy format (matches backend add_issue expectation)
    newIssue = {
        "Name": iName,
        "Issue Name": iName,
        "Priority": priority,
        "Store Number": sNum,
        "Computer Number": compNum,
        "Device": devName,
        "Category": cat,
        "Description": desc,
        "Narrative": "",
        "Replicable?": repro,
        "Status": "Unresolved",
        "Resolution": ""
    }

    payload = {
        "store_name": sName,
        "issue": newIssue
    }

    try:
        response = requests.post(f"{API_BASE}/issues", json=payload, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        print("\n" + c.red(f"Error sending issue to server: {e}"))
        return

    print("\n" + c.green(f"Issue '{iName}' added to {sName} and synced to the server."))


# -----------------------------------
# ISSUE VIEWING
# -----------------------------------

def issueViewOne():
    """View issues for a single store by name or number."""
    stores = get_stores()  # calls GET /stores
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    while True:
        print("\n***** View Issues For One Store *****")
        search_mode = input("Search by store (N)ame or (#) Number? (N/#): ").strip().lower()

        # --- SEARCH BY STORE NAME ---
        if search_mode in ("n", "name"):
            sName_input = input("\nEnter part or all of the store name (e.g., 'Worcester'): ").strip()

            matches = [
                (store_name, details)
                for store_name, details in stores.items()
                if sName_input.lower() in store_name.lower()
            ]

            if not matches:
                print("\n" + c.red("No stores found matching that name."))
            else:
                chosen_name, chosen_details = issueSelectStore(matches)
                sNum = chosen_details.get("Store Number", "Unknown")

                if isinstance(sNum, int):
                    issues = getIssuesForStore(store_number=sNum)
                else:
                    issues = getIssuesForStore(store_name=chosen_name)

                displayIssues(chosen_name, sNum, issues)

        # --- SEARCH BY STORE NUMBER ---
        elif search_mode in ("#", "num", "number"):
            sNum_input = input("\nEnter store number: ").strip()
            try:
                sNum_int = int(sNum_input)
            except ValueError:
                print("\n" + c.red("Store number must be a number."))
            else:
                chosen_name = None

                for store_name, details in stores.items():
                    if details.get("Store Number") == sNum_int:
                        chosen_name = store_name
                        break

                if chosen_name is None:
                    print("\n" + c.red("Store number not found."))
                else:
                    issues = getIssuesForStore(store_number=sNum_int)
                    displayIssues(chosen_name, sNum_int, issues)

        else:
            print("\n" + c.red("Invalid choice. Please enter N for name or # for number."))
            continue

        again = input("\nTry another store? (Y/N): ").strip().lower()
        if again != "y":
            break


def issueViewAll():
    """
    View all issues for all stores.
    This loops over store metadata, and for each store calls /issues/by-store.
    """
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    print("\n***** Stores with Known issues *****\n")
    has_issues = False

    for sName, details in stores.items():
        sNum = details.get("Store Number")
        if sNum is None:
            continue

        issues = getIssuesForStore(store_number=sNum)
        if not issues:
            continue

        has_issues = True
        displayIssues(sName, sNum, issues)
        print("-" * 40)

    if not has_issues:
        print(c.yellow("\nNo stores have reported issues at this time"))


def issueSearch():
    """
    Advanced search menu for issues.
    Lets the user pick a field and enter search parameters,
    then queries the DB via /issues/search.
    """
    while True:
        print("\n********** SEARCH FOR AN ISSUE **********")
        print("\nSearch by any of the following:")
        print("1. Store Number")
        print("2. Category")
        print("3. Status")
        print("4. Device")
        print("5. Name")
        print("6. Exit Search")

        choice = input("\nSelect a search mode (1-6): ").strip()

        if choice == "6":
            print(c.yellow("Exiting search."))
            return

        if choice not in {"1", "2", "3", "4", "5"}:
            print(c.red("Invalid selection. Please choose a number from 1 to 6."))
            continue

        mode = int(choice)

        print("\nEnter Search Parameters:")
        term = input("> ").strip()

        if not term:
            print(c.red("Search term cannot be empty."))
            continue

        # For store number, validate numeric
        if mode == 1:
            if not term.isdigit():
                print(c.red("Store number must be a number."))
                continue

        results = apiSearchIssues(mode, term)
        displaySearchResults(results)

        again = input("\nPerform another search? (Y/N): ").strip().lower()
        if again != "y":
            break


# -----------------------------------
# ISSUE EDIT / UPDATE
# -----------------------------------

def issueResAdd(issue_legacy: dict):
    """Add resolution text to a legacy-style issue dict."""
    res = input("Resolution: ").strip()
    issue_legacy["Resolution"] = res
    print(c.green("Resolution added successfully"))


def issueUpdate():
    """
    Update only status (and optionally resolution) of an issue.
    Uses DB for selection, then sends legacy-style updated_issue to /issues/update.
    """
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    sNum = input("Enter the store number: ").strip()

    # Locate store name from metadata
    sName = None
    sNum_int = None
    try:
        sNum_int = int(sNum)
    except ValueError:
        print(c.red("Store number must be a number."))
        return

    for store, details in stores.items():
        if details.get("Store Number") == sNum_int:
            sName = store
            break

    if not sName:
        print(c.red("Store number not found. Please try again."))
        return

    # Choose an issue from DB rows
    chosen_row = select_issue_for_store(sName, sNum_int)
    if chosen_row is None:
        return

    issue_id = chosen_row.get("id")
    if issue_id is None:
        print(c.red("Selected issue has no 'id'; cannot update."))
        return

    # Build legacy-style issue dict for updating
    issue_legacy = build_legacy_issue_from_db(sName, chosen_row)

    # Prompt for updated status
    statusNew = input("\nEnter the updated status (Unresolved, In Progress, Resolved): ").strip()
    issue_legacy["Status"] = statusNew

    if statusNew.lower() == "resolved":
        addRes = input("\nWould you like to add a resolution for this issue (Y/N)?: ").strip().lower()
        if addRes == "y":
            issueResAdd(issue_legacy)

    print("\n" + c.yellow("Saving changes to server..."))
    if apiUpdate(issue_id, issue_legacy):
        print(c.green("Status updated and synced to cloud."))
    else:
        print(c.red("Failed to update issue on server."))


def issueEdit():
    """
    Edit any attribute of an existing issue.
    Uses DB for selection, then sends legacy-style updated_issue to /issues/update.
    """
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    # 1. PICK STORE
    sName = issueStoreSearch()
    if sName is None:
        print("\n" + c.red("Edit cancelled. Returning to main menu."))
        return

    store_details = stores.get(sName, {})
    sNum = store_details.get("Store Number")

    # 2. PICK ISSUE (from DB)
    chosen_row = select_issue_for_store(sName, sNum)
    if chosen_row is None:
        return

    issue_id = chosen_row.get("id")
    if issue_id is None:
        print(c.red("Selected issue has no 'id'; cannot update."))
        return

    # Build legacy-style editable dict
    issue = build_legacy_issue_from_db(sName, chosen_row)

    # 3. EDIT LOOP
    while True:
        print("\nPlease choose what you wish to edit:")
        print("Name")
        print("Device")
        print("Category")
        print("Computer number")
        print("Description")
        print("Add Narrative")
        print("Resolution")
        print("Status")
        print("Priority")
        print("Exit")

        opt = input("\nYour choice: ").strip().lower()

        # ---- NAME ----
        if "name" in opt and "issue" not in opt and "add" not in opt:
            new_name = input("New Issue Name: ").strip()
            issue["Name"] = new_name
            issue["Issue Name"] = new_name  # keep both keys in sync
            print(c.green(f"Issue name changed to '{new_name}'."))

        # ---- DEVICE ----
        elif "device" in opt:
            new_dev = input("New Device (e.g., Computer, Printer, Phone): ").strip()
            issue["Device"] = new_dev
            print(c.green(f"Device changed to '{new_dev}'."))

        # ---- CATEGORY ----
        elif "category" in opt or opt == "cat":
            new_cat = input("New Category: ").strip()
            issue["Category"] = new_cat
            print(c.green(f"Category changed to '{new_cat}'."))

        # ---- COMPUTER NUMBER ----
        elif "computer" in opt or "comp" in opt:
            new_comp = input("New Computer Number: ").strip()
            issue["Computer Number"] = new_comp
            print(c.green(f"Computer number changed to '{new_comp}'."))

        # ---- DESCRIPTION (overwrite) ----
        elif "description" in opt or "desc" in opt:
            new_desc = input("New Description (this will replace the old one): ").strip()
            issue["Description"] = new_desc
            print(c.green("Description updated."))

        # ---- ADD NARRATIVE (append) ----
        elif "add" in opt or "narrative" in opt:
            print("Add your narrative here (this will be appended):")
            new_narr = input()
            existing = issue.get("Narrative", "")
            if existing:
                issue["Narrative"] = existing + "\n\n" + new_narr
            else:
                issue["Narrative"] = new_narr
            print(c.green("Narrative saved!"))

        # ---- RESOLUTION ----
        elif "resolution" in opt or "res" in opt:
            new_res = input("New Resolution (leave blank to clear): ").strip()
            issue["Resolution"] = new_res
            print(c.green("Resolution updated."))

        # ---- STATUS ----
        elif "status" in opt:
            new_status = input("New Status (e.g., Unresolved, Resolved, In Progress): ").strip()
            issue["Status"] = new_status
            print(c.green(f"Status changed to '{new_status}'."))

        # ---- PRIORITY ----
        elif "priority" in opt or "prio" in opt:
            new_prio = input("New Priority (e.g., 1, 2, 3): ").strip()
            issue["Priority"] = new_prio
            print(c.green(f"Priority changed to '{new_prio}'."))

        # ---- EXIT ----
        elif "exit" in opt or opt == "x":
            print(c.yellow("Exiting issue editor and saving changes..."))
            break

        else:
            print(c.red("Invalid choice. Please type one of the menu options."))
            continue

    # 4. SAVE CHANGES VIA API
    print("\n" + c.yellow("Saving changes to server..."))
    if apiUpdate(issue_id, issue):
        print(c.green("Changes saved."))
    else:
        print(c.red("Changes were NOT saved to the server."))


def issueRemove():
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    sNum = input("Enter the store number: ").strip()

    # Locate store name from metadata
    sName = None
    try:
        sNum_int = int(sNum)
    except ValueError:
        print(c.red("Store number must be a number."))
        return

    for store, details in stores.items():
        if details.get("Store Number") == sNum_int:
            sName = store
            break

    if not sName:
        print(c.red("Store number not found. Please try again."))
        return

    # Choose an issue from DB rows
    chosen_row = select_issue_for_store(sName, sNum_int)
    if chosen_row is None:
        return

    issue_id = chosen_row.get("id")
    if issue_id is None:
        print(c.red("Selected issue has no 'id'; cannot delete."))
        return

    issue_name = chosen_row.get("issue_name") or "Unnamed Issue"
    status = chosen_row.get("status") or "Unresolved"

    print(f"\nYou are about to DELETE this issue:")
    print(f"  Store: {sName} ({sNum_int})")
    print(f"  Issue: {issue_name} [{status}]")
    confirm = input("\nAre you sure? This cannot be undone. (Y/N): ").strip().lower()

    if confirm != "y":
        print(c.yellow("Delete cancelled."))
        return

    print("\n" + c.yellow("Deleting issue on server..."))
    if apiDelete(issue_id):
        print(c.green("Issue successfully deleted from the database."))
    else:
        print(c.red("Issue could not be deleted."))


# -----------------------------------
# ISSUE PRINTING
# -----------------------------------

def issuePrintAll():
    """
    Export all known issues (from DB) grouped by store into a text file.
    """
    stores = get_stores()
    if stores is None:
        print(c.red("Could not connect to server!"))
        return

    print("\nCreating dump file...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(current_dir, "Reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    txt_file_path = os.path.join(reports_dir, "KnownIssuesReport.txt")

    with open(txt_file_path, "w") as txt_file:
        txt_file.write("*****Known Issues Report*****\n\n")
        has_issues = False

        for sName, details in stores.items():
            sNum = details.get("Store Number")
            if sNum is None:
                continue

            issues = getIssuesForStore(store_number=sNum)
            if not issues:
                continue

            has_issues = True

            txt_file.write(f"Store: {sName}\n")
            txt_file.write(f"Store Number: {sNum}\n")
            txt_file.write("Known Issues:\n")

            for idx, issue in enumerate(issues, start=1):
                issue_name = issue.get("issue_name", "Unnamed Issue")
                status = issue.get("status", "Unresolved")
                priority = issue.get("priority", "N/A")
                computer = issue.get("computer_number", "N/A")
                dev_type = issue.get("device_type", "N/A")
                category = issue.get("category", "N/A")
                desc = issue.get("description", "N/A")
                res = issue.get("resolution", "No Resolution Provided")

                txt_file.write(f"  {idx}. {issue_name}\n")
                txt_file.write(f"     Status: {status}\n")
                txt_file.write(f"     Priority: {priority}\n")
                txt_file.write(f"     Computer: {computer}\n")
                txt_file.write(f"     Device: {dev_type}\n")
                txt_file.write(f"     Category: {category}\n")
                txt_file.write(f"     Description: {desc}\n")
                txt_file.write(f"     Resolution: {res}\n")
                txt_file.write("-" * 40 + "\n\n")

        if not has_issues:
            txt_file.write("No known issues reported for any stores at this time.\n")

    print("\n" + c.green(f"Known issues have been exported to {txt_file_path}."))


# -----------------------------------
# MAIN MENU LOOP (MOBILE-FRIENDLY)
# -----------------------------------

while True:
    print("\nWELCOME TO CCT ISSUE TRACKER v2 (Mobile)!")
    print("\nPlease select one of the following options: ")
    print("\nREPORT: Report a new issue")
    print("UPDATE: Update the status of an existing issue")
    print("EDIT: Edit any attribute of an existing issue")
    print("VIEW: View all current issues or all issues in a specific location")
    print("SEARCH: Search for an issue by store, category, status, device, or name")
    print("REMOVE: Delete an existing issue")
    print("PRINT: Export a list of all Known Issues to a text file")
    print("EXIT: Exit the program")

    choice = input("\n: ").upper()

    if choice == "REPORT":
        print("\n***** Report a new issue *****")
        issueAdd()

    elif choice == "EDIT":
        print("\n***** Edit Details *****")
        issueEdit()

    elif choice == "UPDATE":
        print("\n***** Update issue status *****")
        issueUpdate()

    elif choice == "VIEW":
        print("\n***** View issues *****")
        decision = input("Would you like to view all issues (a) or issues for a specific location (s)?: ").lower()
        if decision == "a":
            print("\n***** View all issues *****")
            issueViewAll()
        elif decision == "s":
            print("\n***** View issues by location *****")
            issueViewOne()
        else:
            print(c.red("Invalid selection."))

    elif choice == "SEARCH":
        print("\n***** Search for issues *****")
        issueSearch()

    elif choice == "REMOVE":
        print("\n***** Remove an issue *****")
        issueRemove()

    elif choice == "PRINT":
        issuePrintAll()

    elif choice == "EXIT":
        print("Thank you for using the program! Copyright 2025 ChromaGlow")
        break

    else:
        print(c.red("Invalid selection! Please try again!"))
