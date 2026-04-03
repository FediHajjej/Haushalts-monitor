import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from database import create_connection

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = NOTIFY_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())

        print(f"Email sent: {subject}")
        return True

    except Exception as e:
        print(f"Email failed: {e}")
        return False

def check_upcoming_expenses():
    conn = create_connection()
    cursor = conn.cursor()

    today = date.today()
    reminder_threshold = today + timedelta(days=7)

    # Get all unpaid upcoming expenses
    cursor.execute("""
        SELECT * FROM upcoming_expenses
        WHERE paid = 0
        AND reminder_sent = 0
        AND due_date <= ?
    """, (str(reminder_threshold),))

    upcoming = cursor.fetchall()

    if not upcoming:
        print("No upcoming expenses to notify about.")
        conn.close()
        return

    # Build email
    overdue_items = []
    due_soon_items = []

    for row in upcoming:
        id_, category, amount, description, due_date, reminder_sent, paid = row
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        days_left = (due - today).days

        if days_left < 0:
            overdue_items.append((id_, category, amount, description, due_date, abs(days_left)))
        else:
            due_soon_items.append((id_, category, amount, description, due_date, days_left))

    if not overdue_items and not due_soon_items:
        conn.close()
        return

    # Build HTML email body
    body = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #2c3e50;">🏠 HaushaltsMonitor — Bill Reminder</h2>
        <p>Here is your upcoming expenses summary:</p>
    """

    if overdue_items:
        body += """
        <h3 style="color: #e74c3c;">🔴 Overdue Bills</h3>
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background:#e74c3c; color:white;">
                <th style="padding:8px;">Category</th>
                <th style="padding:8px;">Amount</th>
                <th style="padding:8px;">Due Date</th>
                <th style="padding:8px;">Days Overdue</th>
                <th style="padding:8px;">Description</th>
            </tr>
        """
        for id_, cat, amt, desc, due, days in overdue_items:
            body += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding:8px;">{cat}</td>
                <td style="padding:8px;">€{amt:.2f}</td>
                <td style="padding:8px;">{due}</td>
                <td style="padding:8px; color:#e74c3c;"><b>{days} days overdue</b></td>
                <td style="padding:8px;">{desc or ''}</td>
            </tr>
            """
        body += "</table><br>"

    if due_soon_items:
        body += """
        <h3 style="color: #f39c12;">🟡 Due Within 7 Days</h3>
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background:#f39c12; color:white;">
                <th style="padding:8px;">Category</th>
                <th style="padding:8px;">Amount</th>
                <th style="padding:8px;">Due Date</th>
                <th style="padding:8px;">Days Left</th>
                <th style="padding:8px;">Description</th>
            </tr>
        """
        for id_, cat, amt, desc, due, days in due_soon_items:
            body += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding:8px;">{cat}</td>
                <td style="padding:8px;">€{amt:.2f}</td>
                <td style="padding:8px;">{due}</td>
                <td style="padding:8px; color:#f39c12;"><b>{days} days left</b></td>
                <td style="padding:8px;">{desc or ''}</td>
            </tr>
            """
        body += "</table><br>"

    body += """
        <p style="color:#7f8c8d; font-size:12px;">
            Sent by HaushaltsMonitor — your personal home dashboard
        </p>
    </body>
    </html>
    """

    # Send email
    total = len(overdue_items) + len(due_soon_items)
    subject = f"🏠 HaushaltsMonitor — {total} Bill Reminder{'s' if total > 1 else ''}"
    success = send_email(subject, body)

    # Mark as reminder sent
    if success:
        for row in upcoming:
            id_ = row[0]
            cursor.execute("UPDATE upcoming_expenses SET reminder_sent=1 WHERE id=?", (id_,))
        conn.commit()

    conn.close()

def test_email():
    success = send_email(
        "🏠 HaushaltsMonitor — Test Email",
        "<h2>It works!</h2><p>Your HaushaltsMonitor email notifications are set up correctly.</p>"
    )
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Test email failed — check your .env file")

if __name__ == "__main__":
    test_email()