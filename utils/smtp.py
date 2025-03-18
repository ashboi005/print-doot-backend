import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

# Get email details from environment variables
GMAIL_USER = os.getenv("GMAIL_USER")  # Example: your email (e.g., example@gmail.com)
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Your Gmail App Password or actual password

def send_email(to_email: str, subject: str, body: str):
    """
    Function to send email using Gmail SMTP server
    """
    try:
        # Set up the server and login to the Gmail account
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)

        # Create the email content
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add the body of the email
        msg.attach(MIMEText(body, 'html'))

        # Send the email
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()

        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {e}")
