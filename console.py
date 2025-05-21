# =================================================================================
# Project     : Media Triage
# File        : console.py
# Description : Structured CLI logging with levels, indentation and color
# Author      : Jorge (Blacksheep)
# Created     : 2025-05-20
# =================================================================================

import os
from colorama import init, Fore, Style

init(autoreset=True)

DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), "triage.debug.log")

def write_console(message, level="INFO", indent=0):
    """
    level: INFO, OK, WARN, ERROR, ACTION, TITLE
    indent: 0 = top-level, 1 = sub-item, etc.
    """

    level = level.upper()

    bullets = {
        "INFO": "-",
        "OK": "- [OK]",
        "WARN": "- [!]",
        "ERROR": "- [ERROR]",
        "ACTION": ">",   # Main operational steps
        "TITLE": ">"     # Titles like "Starting..." or "Preloading..."
    }

    colors = {
        "INFO": Fore.WHITE,
        "OK": Fore.GREEN,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "ACTION": Fore.CYAN,
        "TITLE": Fore.CYAN
    }

    bullet = bullets.get(level, "-")
    color = colors.get(level, Fore.LIGHTBLACK_EX)
    prefix = "  " * indent + f"{bullet} "

    print(f"{color}{prefix}{message}{Style.RESET_ALL}")

def write_debug(message):
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def write_delete_line(folder_path, indent=1):
    prefix = "  " * indent + "- [DELETE] "
    print(f"{Fore.RED}{prefix}{folder_path}{Style.RESET_ALL}")
