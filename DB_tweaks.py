import sqlite3
conn = sqlite3.connect("haushalts_monitor.db")
cursor = conn.cursor()

#add notice period and holiday days to job_profiles
try:
    cursor.execute("ALTER TABLE job_profiles ADD COLUMN notice_period TEXT")
    conn.commit()
    print("notice_period added!")
except Exception as e:
    print(f"notice_period: {e}")

try:
    cursor.execute("ALTER TABLE job_profiles ADD COLUMN holiday_days INTEGER")
    conn.commit()
    print("holiday_days added!")
except Exception as e:
    print(f"holiday_days: {e}")

#raise history table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salary_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            old_salary_net REAL,
            new_salary_net REAL,
            old_salary_gross REAL,
            new_salary_gross REAL,
            notes TEXT
        )
    """)
    conn.commit()
    print("salary_history table created!")
except Exception as e:
    print(f"salary_history: {e}")

conn.close()
print("Done!")