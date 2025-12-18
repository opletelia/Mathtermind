#!/usr/bin/env python3
"""
Database Management Script

This script provides a command-line interface for managing the Mathtermind database.
It handles migrations, seeding, and other database operations.

Usage:
    python db_manage.py init      - Initialize the database with the latest schema
    python db_manage.py migrate   - Run all pending migrations
    python db_manage.py seed      - Seed the database with sample data
    python db_manage.py reset     - Reset the database (drop all tables and recreate)
    python db_manage.py status    - Show the current migration status
    python db_manage.py create_migration "message" - Create a new migration
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.core import initialize, get_logger
from src.core.error_handling import (
    DatabaseError, 
    MigrationError, 
    handle_db_errors, 
    create_error_boundary,
    report_error
)

initialize("development")

logger = get_logger(__name__)

from config import DATABASE_PATH, DATA_DIR
from src.db import engine
from src.db.models.base import Base


@handle_db_errors(operation="run_alembic_command")
def run_alembic_command(command, *args):
    """Run an Alembic command with the given arguments."""
    alembic_dir = project_root / "src" / "db"
    
    # Use virtual environment Python if available, otherwise use system Python
    venv_python = project_root / "venv" / "bin" / "python"
    python_cmd = str(venv_python) if venv_python.exists() else "python"
    
    cmd = [python_cmd, "-m", "alembic", command]
    cmd.extend(args)
    
    logger.info(f"Running Alembic command: {' '.join(cmd)}")
    try:
        # Set PYTHONPATH to include the project root so src module can be found
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        result = subprocess.run(cmd, cwd=alembic_dir, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            error_msg = f"Alembic command failed with exit code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr}"
            logger.error(error_msg)
            raise MigrationError(message=error_msg, details={"command": command, "args": args})
        
        if result.stdout:
            logger.debug(f"Command output: {result.stdout}")
            
        return result.returncode
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to execute Alembic command: {str(e)}")
        raise MigrationError(message=f"Failed to execute Alembic command: {str(e)}")


@handle_db_errors(operation="init_db")
def init_db():
    """Initialize the database with the latest schema."""
    logger.info(f"Initializing database at {DATABASE_PATH}...")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    try:
        Base.metadata.create_all(engine)
        logger.info("Database schema created successfully.")
        
        run_alembic_command("stamp", "head")
        logger.info("Database stamped with the current migration version.")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        report_error(e, operation="init_db", database_path=DATABASE_PATH)
        raise


@handle_db_errors(operation="migrate_db")
def migrate_db():
    """Run all pending migrations."""
    logger.info("Running database migrations...")
    return run_alembic_command("upgrade", "head")


@handle_db_errors(operation="seed_db")
def seed_db():
    """Seed the database with sample data."""
    logger.info("Seeding the database with sample data...")
    
    try:
        from src.db.seed import seed_database
        
        with create_error_boundary("seed_database"):
            seed_database()
        
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        logger.error(f"Database seeding failed: {str(e)}")
        report_error(e, operation="seed_db")
        raise


@handle_db_errors(operation="reset_db")
def reset_db():
    """Reset the database (drop all tables and recreate)."""
    logger.info(f"Resetting database at {DATABASE_PATH}...")
    
    try:
        Base.metadata.drop_all(engine)
        logger.info("All tables dropped.")
        
        Base.metadata.create_all(engine)
        logger.info("Database schema recreated successfully.")
        
        run_alembic_command("stamp", "head")
        logger.info("Database stamped with the current migration version.")
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        report_error(e, operation="reset_db", database_path=DATABASE_PATH)
        raise


@handle_db_errors(operation="show_status")
def show_status():
    """Show the current migration status."""
    logger.info("Checking current database migration status:")
    return run_alembic_command("current")


@handle_db_errors(operation="create_migration")
def create_migration(message):
    """Create a new migration."""
    logger.info(f"Creating new migration: {message}")
    return run_alembic_command("revision", "--autogenerate", "-m", message)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Mathtermind Database Management")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    subparsers.add_parser("init", help="Initialize the database with the latest schema")
    subparsers.add_parser("migrate", help="Run all pending migrations")
    subparsers.add_parser("seed", help="Seed the database with sample data")
    subparsers.add_parser("reset", help="Reset the database (drop all tables and recreate)")
    subparsers.add_parser("status", help="Show the current migration status")
    
    create_parser = subparsers.add_parser("create_migration", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")
    
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if getattr(args, "debug", False):
        from src.core import debug_mode
        debug_mode()
        logger.info("Debug logging enabled")
    
    try:
        if args.command == "init":
            init_db()
        elif args.command == "migrate":
            migrate_db()
        elif args.command == "seed":
            seed_db()
        elif args.command == "reset":
            reset_db()
        elif args.command == "status":
            show_status()
        elif args.command == "create_migration":
            create_migration(args.message)
        else:
            parser.print_help()
    except Exception as e:
        logger.critical(f"Command '{args.command}' failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
