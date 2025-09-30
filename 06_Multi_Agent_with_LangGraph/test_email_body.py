import getpass
import smtplib
from email.mime.text import MIMEText

# Test email body content specifically
print("📧 Testing Email Body Content")
print("=" * 50)

# Get Gmail App Password
gmail_password = getpass.getpass("Enter Gmail App Password for yourfriendlyintern1@gmail.com: ")

# Simple test content
subject = "TEST: Articles in Email Body"
from_email = "yourfriendlyintern1@gmail.com"
recipients = ["zmh4616@vt.edu", "bbgold24@vt.edu"]
to_email = ", ".join(recipients)

# Create simple email body with articles
email_body = """TEST EMAIL - Articles Should Be in Body

ARTICLE 1: Washington DC Metro News
====================================
The Washington Metro system announced new service improvements today. 
Riders can expect better frequency and extended hours on key routes.

Read more: https://www.wmata.com

ARTICLE 2: DC Council Updates
============================
The DC Council passed new legislation regarding housing and transportation. 
The new laws aim to improve affordability and accessibility.

Read more: https://www.dccouncil.gov

ARTICLE 3: National Mall Events
===============================
Several cultural events are scheduled this week at the National Mall. 
Visitors can enjoy free concerts and educational programs.

Read more: https://www.nps.gov/nama

---
This is a test email to verify articles appear in the email body.
"""

print("📧 Email Body Content:")
print("=" * 30)
print(email_body)
print("=" * 30)

# Clean password
clean_password = gmail_password.encode('ascii', 'ignore').decode('ascii')

try:
    print(f"\n🚀 Sending test email...")
    
    # Create email message
    msg = MIMEText(email_body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(from_email, clean_password)
        server.send_message(msg)
    
    print("✅ Test email sent successfully!")
    print("📧 Check your inbox - articles should be in the email body")
    print("❌ If you see an attachment, there's an encoding issue")
    print("✅ If you see articles in the email body, it's working!")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("Test complete!")
