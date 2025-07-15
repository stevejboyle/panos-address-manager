#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
from pathlib import Path

# --- Configuration ---
# Use the current directory of the script to locate project files
PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def get_python_executable() -> Path:
    """
    Determines the correct path to the python executable within the venv
    for the current operating system.
    """
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_requirements_file():
    """
    Checks for requirements.txt. If it doesn't exist, creates it
    with 'requests' as the default dependency.
    """
    if not REQUIREMENTS_FILE.exists():
        print(f"[*] '{REQUIREMENTS_FILE.name}' not found. Creating a default one...")
        try:
            with open(REQUIREMENTS_FILE, "w") as f:
                f.write("requests\n")
            print(f"[✓] Created '{REQUIREMENTS_FILE.name}' with 'requests'.")
        except IOError as e:
            print(f"[!] Error creating requirements file: {e}", file=sys.stderr)
            sys.exit(1)


def setup_venv():
    """
    Ensures a virtual environment exists and all dependencies from
    requirements.txt are installed.
    """
    ensure_requirements_file()
    
    # Path to a flag file to check if installation has been run successfully once
    venv_ok_flag = VENV_DIR / ".venv_initialized_ok"

    if venv_ok_flag.exists():
        # Quick check. If the flag exists, we assume venv is okay.
        return

    print("[*] Setting up virtual environment...")
    
    # 1. Create venv if it doesn't exist
    if not VENV_DIR.exists():
        print(f"    - Creating virtual environment in '{VENV_DIR}'...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[!] Failed to create virtual environment: {e}", file=sys.stderr)
            sys.exit(1)

    python_executable = get_python_executable()
    if not python_executable.exists():
        print(f"[!] Virtual environment python not found at '{python_executable}'", file=sys.stderr)
        sys.exit(1)

    # 2. Install dependencies from requirements.txt
    print(f"    - Installing dependencies from '{REQUIREMENTS_FILE.name}'...")
    try:
        # Upgrade pip first
        subprocess.run([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"], check=True, capture_output=True)
        # Install requirements
        subprocess.run([str(python_executable), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=True)
        # Create flag file on success
        venv_ok_flag.touch()
        print("[✓] Virtual environment setup complete.")

    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to install dependencies.", file=sys.stderr)
        print(f"    - Command: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"    - Error: {e.stderr.decode() if e.stderr else 'No stderr'}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to parse arguments and run the selected script."""
    # Define available scripts for the 'action' argument
    scripts = {
        "delete-objects": "delete_address_objects.py",
        "delete-groups": "delete_address_groups.py",
        "create-objects": "create_address_objects.py",
        "create-groups": "create_address_groups.py"
    }

    parser = argparse.ArgumentParser(
        description="A wrapper script to manage PAN-OS address objects and groups.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "examples:\n"
            "  ./panw-wrapper.py delete-objects\n"
            "  ./panw-wrapper.py create-groups"
        )
    )
    parser.add_argument("action", choices=scripts.keys(), help="The action to perform.")
    args = parser.parse_args()

    # Set up the virtual environment and dependencies
    setup_venv()

    script_to_run = PROJECT_ROOT / scripts[args.action]
    if not script_to_run.exists():
        print(f"[!] Error: The script '{script_to_run.name}' does not exist.", file=sys.stderr)
        sys.exit(1)

    python_executable = get_python_executable()
    print(f"\n--- Running '{script_to_run.name}' ---")

    try:
        # Execute the selected script using the venv's python
        # This propagates the return code of the child script.
        process = subprocess.run([str(python_executable), str(script_to_run)], check=False)
        print(f"--- '{script_to_run.name}' finished with exit code {process.returncode} ---")
        sys.exit(process.returncode)

    except KeyboardInterrupt:
        print("\n[!] Script execution interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] An unexpected error occurred while running the script: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
