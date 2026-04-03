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

        return True

    except Exception as e:
        print(f"Email failed: {e}")
        return False

def check_upcoming_expenses():
    conn = create_connection()
    cursor = conn.cursor()

    today = date.today()
    threshold = today + timedelta(days=7)

    cursor.execute("""
        SELECT * FROM upcoming_expenses
        WHERE paid = 0
        AND reminder_sent = 0
        AND due_date <= ?
    """, (str(threshold),))

    upcoming = cursor.fetchall()

    if not upcoming:
        conn.close()
        return

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

    body = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2>HaushaltsMonitor - Bill Reminder</h2>
        <p>Here is your upcoming expenses summary:</p>
    """

    if overdue_items:
        body += """
        <h3 style="color: #c0392b;">Overdue Bills</h3>
        <table style="width:100%; border-collapse: collapse; border: 1px solid #ddd;">
            <tr style="background: #c0392b; color: white;">
                <th style="padding: 10px; text-align:left;">Category</th>
                <th style="padding: 10px; text-align:left;">Amount</th>
                <th style="padding: 10px; text-align:left;">Due Date</th>
                <th style="padding: 10px; text-align:left;">Days Overdue</th>
                <th style="padding: 10px; text-align:left;">Description</th>
            </tr>
        """
        for id_, cat, amt, desc, due, days in overdue_items:
            body += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px;">{cat}</td>
                <td style="padding: 10px;">EUR {amt:.2f}</td>
                <td style="padding: 10px;">{due}</td>
                <td style="padding: 10px; color: #c0392b;"><b>{days} days overdue</b></td>
                <td style="padding: 10px;">{desc or '-'}</td>
            </tr>
            """
        body += "</table><br>"

    if due_soon_items:
        body += """
        <h3 style="color: #d35400;">Due Within 7 Days</h3>
        <table style="width:100%; border-collapse: collapse; border: 1px solid #ddd;">
            <tr style="background: #d35400; color: white;">
                <th style="padding: 10px; text-align:left;">Category</th>
                <th style="padding: 10px; text-align:left;">Amount</th>
                <th style="padding: 10px; text-align:left;">Due Date</th>
                <th style="padding: 10px; text-align:left;">Days Left</th>
                <th style="padding: 10px; text-align:left;">Description</th>
            </tr>
        """
        for id_, cat, amt, desc, due, days in due_soon_items:
            body += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px;">{cat}</td>
                <td style="padding: 10px;">EUR {amt:.2f}</td>
                <td style="padding: 10px;">{due}</td>
                <td style="padding: 10px; color: #d35400;"><b>{days} days left</b></td>
                <td style="padding: 10px;">{desc or '-'}</td>
            </tr>
            """
        body += "</table><br>"

    body += """
        <br>
        <p style="color: #999; font-size: 12px;">
            Sent automatically by HaushaltsMonitor
        </p>
    </body>
    </html>
    """

    total = len(overdue_items) + len(due_soon_items)
    subject = f"HaushaltsMonitor - {total} Bill Reminder{'s' if total > 1 else ''}"
    success = send_email(subject, body)

    if success:
        for row in upcoming:
            cursor.execute(
                "UPDATE upcoming_expenses SET reminder_sent=1 WHERE id=?", (row[0],))
        conn.commit()

    conn.close()

def test_email():
    success = send_email(
        "HaushaltsMonitor - Test Email",
        """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>HaushaltsMonitor</h2>
            <p>Your email notifications are working correctly.</p>
        </body>
        </html>
        """
    )
    return success

if __name__ == "__main__":
    if test_email():
        print("Test email sent successfully")
    else:
        print("Test email failed - check your .env file")