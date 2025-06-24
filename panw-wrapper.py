#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
from pathlib import Path

VENV_DIR = Path(".venv")
PYTHON = VENV_DIR / "bin" / "python"

SCRIPTS = {
    "delete-objects": "delete_address_objects.py",
    "delete-groups": "delete_address_groups.py",
    "create-objects": "create_address_objects.py",
    "create-groups": "create_address_groups.py"
}

def ensure_venv():
    if not VENV_DIR.exists():
        print("[*] Creating .venv virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    print("[*] Installing dependencies into .venv...")
    subprocess.run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(PYTHON), "-m", "pip", "install", "requests"], check=True)

def main():
    parser = argparse.ArgumentParser(
        description="PAN-OS Object/Group Management Wrapper",
        epilog="Example: ./panw-wrapper.py delete-objects"
    )
    parser.add_argument("action", choices=SCRIPTS.keys(), help="Script action to run")
    args = parser.parse_args()

    script = SCRIPTS[args.action]
    script_path = Path(__file__).parent / script

    if not script_path.exists():
        print(f"Error: {script} not found in {script_path.parent}")
        sys.exit(1)

    ensure_venv()
    print(f"[*] Executing {script} inside .venv ...")
    subprocess.run([str(PYTHON), str(script_path)])

if __name__ == "__main__":
    main()