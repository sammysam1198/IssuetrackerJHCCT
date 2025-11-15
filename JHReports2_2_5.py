import json

import os

class c:
    RESET = "\033[0m"

    @staticmethod
    def rgb(r, g, b, text):
        return f"\033[38;2;{r};{g};{b}m{text}{c.RESET}"

    @staticmethod
    def bg(r, g, b, text):
        return f"\033[48;2;{r};{g};{b}m{text}{c.RESET}"

    # Your theme colors:
    @staticmethod
    def yellow(text):
        return c.rgb(255, 237, 13, text)

    @staticmethod
    def blue_bg(text):
        return c.bg(47, 74, 119, text)

    @staticmethod
    def red(text):
        return c.rgb(255, 0, 0, text)

    @staticmethod
    def green(text):
        return c.rgb(0, 255, 0, text)

#Color Variables
BLUE_BG = "\033[48;2;47;74;119m" #JH Blue
YELLOW = "\033[38;2;255;237;13m" #JH Yellow
RESET = "\033[0m"
WHITE = "\033[1;37m"        # Bright white
RED = "\033[1;31m"          # Bold red for errors
GREEN = "\033[1;32m"        # Success message


def fill_blue():
    for _ in range(40):   # 40 rows tall
        print(BLUE_BG + " " * 200 + RESET)  # 200 columns wide

def issueAdd():
    with open("Stores.json", "r") as file:
        stores = json.load(file)

    #COLLECT STORE NUMBERS FROM STORES.JSON
    valid_store_numbers = {details["Store Number"] for details in stores.values()}

    #VARIABLE DECLARATION AND COLLECTION OF DATA
    while True:
        sNum = input("\n" + c.blue_bg(c.yellow("Store number: ")))

        # VALIDATION
        try:
            sNum_int = int(sNum)
        except ValueError:
            print("\n" + c.red("Invalid input! Store number must be a number."))
            continue

        if sNum_int not in valid_store_numbers:
            print("\n" + c.red("Store number not found! Please enter a valid number."))
            continue

        #if we reach here then the store number is valid
        break

    devName = input("\n" + c.blue_bg(c.yellow("What type of device is experiencing the issue? (e.g., Phone, Computer etc.): "))).strip()

    compNum = "N/A"
    if "computer" in devName.lower():
        compNum = input("\n" + c.blue_bg(c.yellow("Computer experiencing the issue: ")))

    cat = input("\n" + c.blue_bg(c.yellow("Issue Category: ")))
    priority = input("\n1. Critical\n2. Functional\n3. Cosmetic:\n\nPriority: ")
    desc = input("\n" + c.blue_bg(c.yellow("Describe the issue: ")))
    repro = input("\n" + c.blue_bg(c.yellow("Has this issue been reproduced on any other systems (Yes/No)?: ")))
    iName = input("\n" + c.blue_bg(c.yellow("Give this issue a name: ")))

    sName = None
    for store, details in stores.items():
        if str(details["Store Number"]) == sNum:
            sName = store
            break

    if not sName:
        print("\n" + c.red("Store number not found! Please try again"))
        return

    #define new issue
    newIssue = {
        "Issue Name": iName,
        "Priority": priority,
        "Store Number": sNum,
        "Computer Number": compNum,
        "Type": cat,
        "Description": desc,
        "Narrative": "",
        "Replicable?": repro,
        "Status": "Unresolved",
        "Resolution": ""
    }

    #ADD ISSUE TO FILe
    stores[sName] ["Known Issues"].append(newIssue)

    #SAVE THE DATA YOU JUST ADDED TO THE JSON FILE:
    with open("Stores.json", "w") as file:
        json.dump(stores, file, indent=4)

    print("\n" + c.green(f"Issue '{iName}' added to {sName}"))

def issueStoreSearch(stores):
    with open("Stores.json", "r") as file:
        stores = json.load(file)

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

def issueResAdd(issue):
    res = input("Resolution: ").strip()
    issue["Resolution"] = res
    print(c.green("Resolution added successfully"))

def issueUpdate():
    # Load the JSON file
    with open("Stores.json", "r") as file:
        stores = json.load(file)

    # Prompt for store number
    sNum = input("Enter the store number: ").strip()
    sName = None

    # Find the store by its store number
    for store, details in stores.items():
        if str(details["Store Number"]) == sNum:
            sName = store
            break

    if not sName:
        print(c.red("Store number not found. Please try again."))
        return

    # Retrieve known issues for the selected store
    knownIssues = stores[sName].get("Known Issues", [])
    if not knownIssues:
        print(c.yellow(f"No known issues for {sName}."))
        return

    # Display the known issues
    print(f"\nKnown Issues for {sName} (Store Number: {sNum}):")
    for idx, issue in enumerate(knownIssues, start=1):
        print(f"{idx}. Computer: {issue.get('Computer Number', 'N/A')}, "
              f"Type: {issue.get('Type', 'N/A')}, "
              f"Status: {issue.get('Status', 'Unresolved')}")

    # Prompt user for the issue number
    try:
        issueNumber = int(input("\nEnter the issue number to update: ").strip()) - 1
        if issueNumber < 0 or issueNumber >= len(knownIssues):
            print(c.red("\nInvalid issue number. Please try again."))
            return
    except ValueError:
        print(c.red("\nInvalid input. Please enter a number."))
        return

    # Prompt for the updated status
    statusNew = input("\nEnter the updated status (Unresolved, In Progress, Resolved): ").strip()
    knownIssues[issueNumber]["Status"] = statusNew  # Update the status

    if statusNew.lower() == "resolved":
        addRes = input("\nWould you like to add a resolution for this issue (Y/N)?: ").strip().lower()
        if addRes == "y":
            issueResAdd(knownIssues[issueNumber])

    # Save the updated data back to the JSON file
    with open("Stores.json", "w") as file:
        json.dump(stores, file, indent=4)

    print(c.green(f"\nStatus updated for issue #{issueNumber + 1} in {sName}."))

def issueViewAll():
    with open("Stores.json", "r") as file:
        stores = json.load(file)

    print("\n" + c.blue_bg(c.yellow("*****Stores with Known issues*****\n")))
    has_issues = False

    #look thru the stores entries
    for sName, details in stores.items():
        if len(details.get("Known Issues", [])) > 0:
            has_issues = True
            print(f"Store: {sName}")
            print(f"Store Number: {details['Store Number']}")
            print("Known Issues")
            for idx, issue in enumerate(details["Known Issues"], start=1):
                status = issue.get("Status", "Unresolved")
                if status.lower() == "resolved":
                    res = issue.get("Resolution", "None Provided")
                    print(f"\n{idx}. [Resolved] {issue['Type']}\nResolution: {res}")
                else:
                    print(f"\n{idx}. [{status}] {issue['Type']}\nDescription: {issue['Description']}")

            print("-" * 40)

    if not has_issues:
        print(c.yellow("\nNo stores have reported issues at this time"))

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

def issueViewOne():
    """View issues for a single store by name or number."""
    with open("Stores.json", "r") as file:
        stores = json.load(file)

    while True:
        print("\n" + c.blue_bg(c.yellow("***** View Issues For One Store *****")))
        search_mode = input("Search by store (N)ame or (#) Number? (N/#): ").strip().lower()

        # --- SEARCH BY STORE NAME ---
        if search_mode in ("n", "name"):
            sName_input = input("\nEnter part or all of the store name (e.g., 'Worcester'): ").strip()

            # Find all stores whose name contains the input (case-insensitive)
            matches = [
                (store_name, details)
                for store_name, details in stores.items()
                if sName_input.lower() in store_name.lower()
            ]

            if not matches:
                print("\n" + c.red("No stores found matching that name."))
            else:
                # use your existing helper that picks SF/WM etc.
                chosen_name, chosen_details = issueSelectStore(matches)

                # ---------- INLINE "display_store_issues" LOGIC ----------
                sNum = chosen_details.get("Store Number", "Unknown")
                issues = chosen_details.get("Known Issues", [])

                print(f"\n{chosen_name} {sNum}")
                print("Known Issues:")

                if not issues:
                    print(c.yellow("No issues for this store!"))
                else:
                    for idx, issue in enumerate(issues, start=1):
                        issue_name = issue.get("Issue Name") or issue.get("Type") or "Unnamed Issue"
                        status = issue.get("Status", "Unresolved")
                        desc = issue.get("Description", "No description provided")
                        res = issue.get("Resolution", "None Provided")

                        print(f"\n{idx}. {issue_name} [{status}]")
                        if status.lower() == "resolved":
                            print(f"Resolution: {res}")
                        else:
                            print(f"Description: {desc}")

                    print(f"\nnumber of issues: {len(issues)}")
                # --------------------------------------------------------

        # --- SEARCH BY STORE NUMBER ---
        elif search_mode in ("#", "num", "number"):
            sNum_input = input("\nEnter store number: ").strip()
            try:
                sNum_int = int(sNum_input)
            except ValueError:
                print("\n" + c.red("Store number must be a number."))
            else:
                chosen_name = None
                chosen_details = None

                for store_name, details in stores.items():
                    if details.get("Store Number") == sNum_int:
                        chosen_name, chosen_details = store_name, details
                        break

                if chosen_name is None:
                    print("\n" + c.red("Store number not found."))
                else:
                    # ---------- INLINE "display_store_issues" LOGIC ----------
                    sNum = chosen_details.get("Store Number", "Unknown")
                    issues = chosen_details.get("Known Issues", [])

                    print(f"\n{chosen_name} {sNum}")
                    print("Known Issues:")

                    if not issues:
                        print(c.yellow("No issues for this store!"))
                    else:
                        for idx, issue in enumerate(issues, start=1):
                            issue_name = issue.get("Issue Name") or issue.get("Type") or "Unnamed Issue"
                            status = issue.get("Status", "Unresolved")
                            desc = issue.get("Description", "No description provided")
                            res = issue.get("Resolution", "None Provided")

                            print(f"\n{idx}. {issue_name} [{status}]")
                            if status.lower() == "resolved":
                                print(f"Resolution: {res}")
                            else:
                                print(f"Description: {desc}")

                        print(f"\nnumber of issues: {len(issues)}")
                    # --------------------------------------------------------

        else:
            print("\n" + c.red("Invalid choice. Please enter N for name or # for number."))
            continue  # back to top of while True

        # Ask if they want to look up another store
        again = input("\nTry another store? (Y/N): ").strip().lower()
        if again != "y":
            break

def issueEdit():
    with open("Stores.json", "r") as file:
        stores = json.load(file)

    # 1. PICK STORE
    sName = issueStoreSearch(stores)
    if sName is None:
        print("\n" + c.red("Edit cancelled. Returning to main menu."))
        return

    store_details = stores.get(sName, {})
    issues = store_details.get("Known Issues", [])

    if not issues:
        print("\n" + c.yellow(f"{sName} has no issues to edit."))
        return

    # 2. PICK ISSUE
    print(f"\nIssues for {sName} (Store {store_details.get('Store Number', 'Unknown')}):")
    for idx, issue in enumerate(issues, start=1):
        issue_name = issue.get("Issue Name", "Unnamed Issue")
        status = issue.get("Status", "Unresolved")
        print(f"{idx}. {issue_name} [{status}]")

    while True:
        choice = input("\nSelect an issue number to edit: ").strip()
        if choice.isdigit():
            issue_index = int(choice)
            if 1 <= issue_index <= len(issues):
                break
        print(c.red("Invalid selection. Please enter a valid issue number."))

    issue = issues[issue_index - 1]

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
            issue["Issue Name"] = new_name
            print(c.green(f"Issue name changed to '{new_name}'."))

        # ---- DEVICE ----
        elif "device" in opt:
            new_dev = input("New Device (e.g., Computer, Printer, Phone): ").strip()
            issue["Device Name"] = new_dev
            print(c.green(f"Device changed to '{new_dev}'."))

        # ---- CATEGORY (maps to 'Type') ----
        elif "category" in opt or opt == "cat":
            new_cat = input("New Category: ").strip()
            issue["Type"] = new_cat
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

    # 4. SAVE CHANGES BACK TO JSON
    with open("Stores.json", "w") as file:
        json.dump(stores, file, indent=4)

    print("\n" + c.green("Changes saved."))

def issuePrintAll():
    with open("Stores.json", "r") as file:
        stores = json.load(file)

    print("\nCreating dump file")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(current_dir, "Reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    txt_file_path = os.path.join(reports_dir, "KnownIssuesReport.txt")

    with open(txt_file_path, "w") as txt_file:
        txt_file.write("*****Known Issues Report*****\n\n")
        has_issues = False

        for sName, details in stores.items():
            knownIssues = details.get("Known Issues", [])
            if len(knownIssues) > 0:
                has_issues = True

                txt_file.write(f"Store: {sName}\n")
                txt_file.write(f"Store Number: {details['Store Number']}\n")
                txt_file.write("Known Issues: \n")
                for idx, issue in enumerate(knownIssues, start=1):
                    issue_name = issue.get("Issue Name", "Unnamed Issue")

                    txt_file.write(f"  {idx}. {issue_name}\n")
                    txt_file.write(f"     Status: {issue.get('Status', 'Unresolved')}\n")
                    txt_file.write(f"     Priority: {issue.get('Priority', 'N/A')}\n")
                    txt_file.write(f"     Computer: {issue.get('Computer Number', 'N/A')}\n")
                    txt_file.write(f"     Type: {issue.get('Type', 'N/A')}\n")
                    txt_file.write(f"     Description: {issue.get('Description', 'N/A')}\n")
                    txt_file.write(f"     Resolution: {issue.get('Resolution', 'No Resolution Provided')}\n")
                    txt_file.write("-" * 40 + "\n\n")

        if not has_issues:
            txt_file.write("No known issues reported for any stores at this time.\n")


    print("\n" + c.green(f"Known issues have been exported to {txt_file_path}."))






while True:
    print(BLUE_BG + YELLOW + "WELCOME TO CCT ISSUE TRACKER v2!")
    print("\n\nPlease select one of the following options: ")
    print("\nREPORT: Report a new issue")
    print("UPDATE: Update the status of an existing issue")
    print("EDIT: Edit any attribute of an existing issue")
    print("VIEW: View all current issues or all issues in a specific location")
    print("PRINT: Export a list of all Known Issues to a text file")
    print("EXIT: Exit the program")

    choice = input(RESET + "\n: ").upper()

    if choice == "REPORT":
        print("\n" + c.blue_bg(c.yellow("*****Report a new issue*****")))
        issueAdd()

    elif choice == "EDIT":
        print("\n" + c.blue_bg(c.yellow("*****Edit Details*****")))
        issueEdit()

    elif choice == "UPDATE":
        print("\n" + c.blue_bg(c.yellow("*****Update issue status*****")))
        issueUpdate()

    elif choice == "VIEW":
        print("\n" + c.blue_bg(c.yellow("*****View issues*****")))
        decision = input("Would you like do view all issues (a) or issues for a specific location (s)?: ").lower()
        if decision == "a":
            print("\n" + c.blue_bg(c.yellow("*****View all issues*****")))
            issueViewAll()

        elif decision == "s":
            print("\n" + c.blue_bg(c.yellow("*****View issues by location*****")))
            issueViewOne()

    elif choice == "PRINT":
        issuePrintAll()

    elif choice == "EXIT":
        print(c.blue_bg(c.yellow("Thank you for using the program! Copyright 2025 ChromaGlow")))
        break

    else:
        print(c.red("Invalid selection! please try again!"))

