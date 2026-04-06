import sqlite3
from pathlib import Path

DB_NAME = "haushalts_monitor.db"


def create_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Create and return a SQLite connection."""
    return sqlite3.connect(db_path)


def create_tables(db_path: str = DB_NAME) -> None:
    """Create the full HaushaltsMonitor database schema with no seed data."""
    conn = create_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            gas_reading REAL,
            electricity_reading REAL,
            notes TEXT,
            electricity_kwh REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internet_speed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            download REAL,
            upload REAL,
            ping REAL,
            time_of_day TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            notes TEXT,
            expiry_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            table_name TEXT NOT NULL,
            entry_id INTEGER NOT NULL,
            field_changed TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            person TEXT NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurring_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payslips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL,
            month TEXT NOT NULL,
            file_path TEXT NOT NULL,
            amount REAL,
            notes TEXT,
            uploaded_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT UNIQUE NOT NULL,
            employer TEXT,
            job_title TEXT,
            contract_type TEXT,
            start_date TEXT,
            salary_net REAL,
            salary_gross REAL,
            hours_per_week REAL,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paid_bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            paid INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upcoming_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            reminder_sent INTEGER DEFAULT 0,
            paid INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def recreate_database(db_path: str = DB_NAME) -> None:
    """
    Delete the database file if it exists and recreate the full schema.
    Use this only when you want a completely empty fresh database.
    """
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
    create_tables(db_path)


if __name__ == "__main__":
    create_tables()
    print(f"Database schema created successfully in '{DB_NAME}'")
