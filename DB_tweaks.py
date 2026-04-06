import sqlite3
conn = sqlite3.connect("haushalts_monitor.db")
cursor = conn.cursor()

tables = [
    """CREATE TABLE IF NOT EXISTS recurring_income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person TEXT NOT NULL,
        source TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        active INTEGER DEFAULT 1
    )""",

    """CREATE TABLE IF NOT EXISTS payslips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person TEXT NOT NULL,
        month TEXT NOT NULL,
        file_path TEXT NOT NULL,
        amount REAL,
        notes TEXT,
        uploaded_date TEXT NOT NULL
    )""",

    """CREATE TABLE IF NOT EXISTS job_profiles (
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
    )"""
]

for table in tables:
    try:
        cursor.execute(table)
        conn.commit()
        print(f"Table created!")
    except Exception as e:
        print(f"Error: {e}")

conn.close()
print("All done!")