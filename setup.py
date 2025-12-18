#!/usr/bin/env python3
"""
Mathtermind Setup Script

This script helps to set up the Mathtermind project by:
1. Creating a virtual environment (if it doesn't exist)
2. Installing dependencies
3. Setting up the database
4. Creating a .env file (if it doesn't exist)

Usage:
    python setup.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and return its exit code."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    return result.returncode


def setup_virtual_environment():
    """Set up a virtual environment if it doesn't exist."""
    if os.path.exists("venv"):
        print("Virtual environment already exists.")
        return True

    print("Creating virtual environment...")
    exit_code = run_command("python -m venv venv")
    if exit_code != 0:
        print("Failed to create virtual environment.")
        return False

    print("Virtual environment created successfully.")
    return True


def install_dependencies():
    """Install dependencies from requirements.txt."""
    print("Installing dependencies...")

    if sys.platform == "win32":
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        python_path = os.path.join("venv", "bin", "python")

    exit_code = run_command(f"{python_path} -m pip install -r requirements.txt")
    if exit_code != 0:
        print("Failed to install dependencies.")
        return False

    print("Dependencies installed successfully.")
    return True


def setup_database():
    """Set up the database."""
    print("Setting up the database...")

    if sys.platform == "win32":
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        python_path = os.path.join("venv", "bin", "python")

    print("Initializing the database...")
    exit_code = run_command(f"{python_path} db_manage.py init")
    if exit_code != 0:
        print("Failed to initialize the database.")
        return False

    print("Seeding the database...")
    exit_code = run_command(f"{python_path} db_manage.py seed")
    if exit_code != 0:
        print("Failed to seed the database.")
        return False

    print("Database set up successfully.")
    return True


def create_env_file():
    """Create a .env file if it doesn't exist."""
    if os.path.exists(".env"):
        print(".env file already exists.")
        return True

    print("Creating .env file...")
    try:
        shutil.copy(".env.example", ".env")
        print(".env file created successfully.")
        return True
    except Exception as e:
        print(f"Failed to create .env file: {e}")
        return False


def main():
    """Main entry point for the script."""
    print("Setting up Mathtermind...")

    if not setup_virtual_environment():
        return

    if not install_dependencies():
        return

    if not create_env_file():
        return

    if not setup_database():
        return

    print("\nSetup completed successfully!")
    print("\nTo run the application:")
    if sys.platform == "win32":
        print("1. Activate the virtual environment: venv\\Scripts\\activate")
        print("2. Run the application: python main.py")
    else:
        print("1. Activate the virtual environment: source venv/bin/activate")
        print("2. Run the application: python main.py")


if __name__ == "__main__":
    main()
