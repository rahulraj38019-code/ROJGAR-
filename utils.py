import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email Configuration
# Note: Google Account ki 'App Password' settings se password lena hoga
EMAIL_ADDRESS = "aapka-email@gmail.com" 
EMAIL_PASSWORD = "your-app-password" 

def send_job_notification(user_email, user_name, job_title, job_link):
    """Naye job ki jankari email par bhejne ke liye"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = user_email
        msg['Subject'] = f"New Job Alert: {job_title} 🚀"

        body = f"""
        Namaste {user_name},
        
        R YADAV PRODUCTION - ROZGAR APP par ek naya update aaya hai!
        
        Job/Result: {job_title}
        Check karein: {job_link}
        
        Best of Luck,
        Rahul Raj (Rozgar AI)
        """
        
        msg.attach(MIMEText(body, 'plain'))

        # Server connect karke mail bhejna
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, user_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False