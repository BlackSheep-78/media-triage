# =================================================================================
# Project     : Media Triage
# File        : triage.py
# Description : Skeleton version of triage.ps1 rewritten in Python
# Author      : Jorge (Blacksheep)
# Created     : 2025-05-20
# =================================================================================

import string
import json
import os
import random
import sys
import shutil
import time

from uuid import uuid4
from console import write_console
from console import write_debug
from console import write_delete_line
from ctypes import windll

DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), "triage.debug.log")

folders_marked_for_deletion = []


def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        write_console(f"[FATAL] Failed to load config.json: {e}")
        sys.exit(1)

def validate_paths(config):
    missing = False

    paths_to_check = {
        "python_path": config.get("python_path"),
        "triage_script": config.get("triage_script"),
        "log_file (parent dir)": os.path.dirname(config.get("log_file", "")),
        "inbox_path": config.get("inbox_path"),
    }

    write_console("Preloading configuration paths", "TITLE")

    for name, path in paths_to_check.items():
        if not path or not os.path.exists(path):
            write_console(f"Path missing or invalid: {name} → {path}", "ERROR", indent=1)
            missing = True
        else:
            write_console(f"Valid path: {name} → {path}", "OK", indent=1)

    if missing:
        write_console("One or more required paths are missing. Aborting.", "ERROR")
        sys.exit(1)

def initialize_triage(config):
    root_path = os.path.dirname(config["inbox_path"])
    inbox_path = config["inbox_path"]

    write_console("Starting Media Triage", "TITLE")
    write_console(f"Root Path: {root_path}", "INFO", indent=1)
    write_console(f"INBOX Path: {inbox_path}", "INFO", indent=1)

    # Create INBOX folder if missing
    if not os.path.exists(inbox_path):
        os.makedirs(inbox_path)
        write_console(f"Created INBOX folder at: {inbox_path}", "OK", indent=1)
    else:
        write_console("INBOX folder already exists.", "OK", indent=1)

    # Create logs folder in project root
    project_root = os.path.dirname(__file__)
    logs_path = os.path.join(project_root, "logs")
    os.makedirs(logs_path, exist_ok=True)
    write_console(f"Logs folder verified: {logs_path}", "OK", indent=1)

    # Attach runtime path to config["system"]
    config["system"] = {
        "logs_path": logs_path
    }

def generate_human_name():
    adjectives = ["Silver", "Crimson", "Midnight", "Blue", "Quiet", "Stormy", "Velvet"]
    animals = ["Falcon", "Goose", "Panther", "Fox", "Whale", "Wolf", "Jackal"]
    return f"{random.choice(adjectives)} {random.choice(animals)}"

def detect_external_drives():
    write_console("Detecting external sources", "TITLE")

    valid_drives = []

    # Windows only: detect removable drives
    removable_drives = [f"{letter}:\\"
                        for letter in string.ascii_uppercase
                        if windll.kernel32.GetDriveTypeW(f"{letter}:\\") == 2]

    if not removable_drives:
        write_console("No removable drives detected.", "WARN", indent=1)

    for drive in removable_drives:
        write_console(f"Found drive: {drive}", "INFO", indent=1)
        drive_json_path = os.path.join(drive, "drive.json")

        if os.path.exists(drive_json_path):
            write_console("drive.json found", "OK", indent=2)

            try:
                with open(drive_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                write_console(f"Failed to read drive.json: {e}", "ERROR", indent=2)
                continue

            if data.get("source") is not True:
                write_console("'source' is not set to true. Skipping drive.", "WARN", indent=2)
                continue

            updated = False

            if "id" not in data:
                data["id"] = str(uuid4())
                updated = True

            if "name" not in data:
                data["name"] = generate_human_name()
                updated = True

            if updated:
                try:
                    with open(drive_json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    write_console(f"Drive baptized as: {data['name']} ({data['id']})", "OK", indent=2)
                except Exception as e:
                    write_console(f"Failed to write updated drive.json: {e}", "ERROR", indent=2)
                    continue
            else:
                write_console(f"Drive already baptized: {data['name']} ({data['id']})", "INFO", indent=2)

            valid_drives.append({
                "path": drive,
                "id": data["id"],
                "name": data["name"],
                "json": data
            })
        else:
            write_console("No drive.json found. Skipping.", "INFO", indent=2)

    return valid_drives

def backup_media_file(file_path, drive_info):
    write_console(f"[DRY RUN] Would backup: {file_path} from {drive_info['name']}", "INFO", indent=2)

def try_remove_folder(folder_path, drive_info):
    write_debug(f"[CALL] try_remove_folder → {folder_path}")

    has_media = False
    has_subfolders = False
    media_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".heic", ".mp4", ".mov", ".avi", ".mkv"]

    try:
        entries = list(os.scandir(folder_path))
    except Exception as e:
        write_debug(f"[ERROR] Cannot access {folder_path}: {e}")
        return

    for entry in entries:
        if entry.is_dir():
            has_subfolders = True
        elif entry.is_file():
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in media_exts:
                has_media = True

    if not has_media and not has_subfolders:
        folders_marked_for_deletion.append(folder_path)
        write_delete_line(folder_path, indent=2)
        write_debug(f"[MARKED] {folder_path} marked for deletion")

def import_from_external_drives(drives):
    write_console("Importing from external drives", "TITLE")
    media_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".heic", ".mp4", ".mov", ".avi", ".mkv"]

    for drive in drives:
        root_path = drive["path"]
        drive_name = drive["name"]
        json_data = drive["json"]
        purge = json_data.get("purge", False)

        write_debug(f"[DEBUG CONFIG] drive JSON raw: {json_data}")

        write_console(f"Processing drive: {drive_name}", "ACTION", indent=1)

        for root, dirs, files in os.walk(root_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in media_exts:
                    full_path = os.path.join(root, file)
                    backup_media_file(full_path, drive)

            write_debug(f"[BEFORE PURGE] Purge is active in {root}")
            write_debug(f"[PURGE] =  {purge}")
            if purge:
                # Fix: Normalize paths to compare properly
                write_debug(f"[AFTER PURGE] Purge is active in {root}")
                write_debug(f"CHECK: comparing root={root} vs root_path={root_path}")
                try:
                    if os.path.normpath(root) != os.path.normpath(root_path):
                        try_remove_folder(root, drive)
                    else:
                        write_debug(f"✘ PATHS MATCH → skipping {root}")
                except Exception as e:
                    write_debug(f"[ERROR] samefile() exception: {e}")

def get_root_files():
    write_console("Getting files in root folder...")
    # Future: return list of files


def copy_with_hash_check(source, destination):
    write_console(f"Copying with hash check: {source} → {destination}")
    # Future: copy + SHA256 + verify
    return True


def move_to_inbox(files):
    write_console(f"Moving {len(files)} files to INBOX folders...")
    # Future: find slots in 00–99 folders and move files


def refill_from_inbox():
    write_console("Refilling root folder from INBOX...")
    # Future: move files back to root if under limit

def recover_failed_copies():
    write_console("Attempting recovery of failed copies from log...")
    # Future: scan triage.log and retry failed files

def show_deletion_summary():
    if folders_marked_for_deletion:
        write_console("===" * 10, "ERROR")
        write_console(" FOLDERS MARKED FOR DELETION ", "ERROR")
        write_console("===" * 10, "ERROR")
        for folder in folders_marked_for_deletion:
            write_console(f"- {folder}", "ERROR", indent=1)

def confirm_and_delete_folders(config):
    deletion_log = os.path.join(config["system"]["logs_path"], "folders_to_delete.log")
    if not os.path.exists(deletion_log):
        return

    with open(deletion_log, "r", encoding="utf-8") as f:
        folders = [line.strip() for line in f if line.strip()]

    if not folders:
        return

    write_console(f"Deleting {len(folders)} folders...", "TITLE")

    total = len(folders)
    width = 50

    for i, folder in enumerate(folders, 1):
        try:
            shutil.rmtree(folder)
        except Exception as e:
            write_debug(f"[DELETE ERROR] {folder}: {e}")

        if i > 1:
            print("\033[F\033[F", end="")  # move up 2 lines

        # Clear both lines
        print(" " * 100, end="\r")
        print(" " * 100, end="\r")

        # Draw progress bar
        progress = int((i / total) * width)
        bar = "[" + "#" * progress + "-" * (width - progress) + f"] {i}/{total}"
        print(bar.ljust(100))

        # Print current folder being deleted
        print(f"Deleting: {folder}".ljust(100), end="\r", flush=True)

        time.sleep(0.01)

    # Final cleanup
    print("\033[F\033[F", end="")        # Move up
    print(" " * 100, end="\r")           # Clear bar
    print(" " * 100, end="\r")           # Clear folder
    write_console("Folder deletion completed.", "OK")





def finalize_purge_log_and_delete(config):
    if not folders_marked_for_deletion:
        return
    write_folders_to_delete_log(config)
    confirm_and_delete_folders(config)

def write_folders_to_delete_log(config):
    deletion_log = os.path.join(config["system"]["logs_path"], "folders_to_delete.log")
    with open(deletion_log, "w", encoding="utf-8") as f:
        for folder in folders_marked_for_deletion:
            f.write(folder + "\n")
    write_console(f"Wrote list of folders to delete: {deletion_log}", "OK", indent=1)

def main():
    # Clear debug log at start
    open(DEBUG_LOG_PATH, "w").close()

    config = load_config()
    validate_paths(config)
    initialize_triage(config)

    drives = detect_external_drives()
    import_from_external_drives(drives)

    root_files = get_root_files()
    write_console(f"Loose files detected: [placeholder count]", "INFO")

    refill_from_inbox()
    recover_failed_copies()

    finalize_purge_log_and_delete(config)

    write_console("=== Triage Completed ===", "OK")




if __name__ == "__main__":
    main()
