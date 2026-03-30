from database import create_connection
from datetime import datetime

def add_energy_reading(gas_reading, electricity_reading, notes=""):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO energy (date, gas_reading, electricity_reading, notes)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d"), gas_reading, electricity_reading, notes))
    conn.commit()
    conn.close()
    print(f"Energy reading saved!")

def add_expense(category, amount, description=""):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (date, category, amount, description)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d"), category, amount, description))
    conn.commit()
    conn.close()
    print(f"Expense saved!")

def add_speed_test(download, upload, ping):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO internet_speed (date, download, upload, ping)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d"), download, upload, ping))
    conn.commit()
    conn.close()
    print(f"Speed test saved!")

if __name__ == "__main__":
    # Test data so we have something to show on the dashboard
    add_energy_reading(1523.5, 342.1, "January reading")
    add_energy_reading(1587.2, 358.4, "February reading")
    add_energy_reading(1634.8, 371.2, "March reading")
    
    add_expense("Miete", 650, "Monthly rent")
    add_expense("Strom", 89.50, "Electricity bill")
    add_expense("Gas", 120.00, "Gas bill")
    add_expense("Internet", 39.99, "Vodafone")
    add_expense("Lebensmittel", 280.00, "Groceries March")
    
    add_speed_test(45.2, 12.1, 24)
    add_speed_test(38.7, 10.3, 31)
    add_speed_test(52.1, 14.8, 18)
    
    print("All test data inserted!")
