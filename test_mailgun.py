import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Mailgun SMTP configuration (use environment variables for security)
MAILGUN_SMTP_HOST = os.getenv("MAILGUN_SMTP_HOST", "smtp.eu.mailgun.org")
MAILGUN_SMTP_PORT = int(os.getenv("MAILGUN_SMTP_PORT", "587"))
MAILGUN_SMTP_USERNAME = os.getenv("MAILGUN_SMTP_USERNAME", "postmaster@mg.tarikcoralic.me")
MAILGUN_SMTP_PASSWORD = os.getenv("MAILGUN_SMTP_PASSWORD", "")  # Set this via environment variable
MAILGUN_FROM_EMAIL = os.getenv("MAILGUN_FROM_EMAIL", "postmaster@mg.tarikcoralic.me")
MAILGUN_FROM_NAME = os.getenv("MAILGUN_FROM_NAME", "SSSD Project")

def test_mailgun_smtp():
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{MAILGUN_FROM_NAME} <{MAILGUN_FROM_EMAIL}>"
        msg['To'] = "test@example.com"
        msg['Subject'] = "Test Email from Python SMTP"
        
        # Add body to email
        body = "This is a test email sent via SMTP from Python, just like your PHP project!"
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        print(f"Connecting to {MAILGUN_SMTP_HOST}:{MAILGUN_SMTP_PORT}...")
        server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT)
        
        print("Starting TLS...")
        server.starttls()  # Enable TLS
        
        print(f"Logging in with username: {MAILGUN_SMTP_USERNAME}")
        server.login(MAILGUN_SMTP_USERNAME, MAILGUN_SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        print("Sending email...")
        server.sendmail(MAILGUN_FROM_EMAIL, "test@example.com", text)
        server.quit()
        
        print("✅ Email sent successfully via SMTP!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email via SMTP: {e}")
        return False

if __name__ == "__main__":
    print("Testing Mailgun SMTP (same as your PHP project)...")
    test_mailgun_smtp() 