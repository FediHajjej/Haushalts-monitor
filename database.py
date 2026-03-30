import sqlite3
from datetime import datetime

def create_connection():
    conn = sqlite3.connect("haushalts_monitor.db")
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    
    # Gas/Energy table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            gas_reading REAL,
            electricity_reading REAL,
            notes TEXT
        )
    """)
    
    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    """)
    
    # Internet speed table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internet_speed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            download REAL,
            upload REAL,
            ping REAL
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database and tables created successfully!")

if __name__ == "__main__":
    create_tables()