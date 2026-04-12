import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email Configuration
# Google Account -> Security -> 2-Step Verification -> App Passwords
EMAIL_ADDRESS = "aapka-email@gmail.com" 
EMAIL_PASSWORD = "your-app-password" 

def send_job_notification(user_email, user_name, job_title, job_link):
    """Naye job ki jankari email par bhejne ke liye (HTML Support)"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Rozgar AI - R YADAV PRODUCTION <{EMAIL_ADDRESS}>"
        msg['To'] = user_email
        msg['Subject'] = f"🔥 New Job Update: {job_title}"

        # HTML Body taaki email professional lage
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
                    <h2 style="color: #172554;">Namaste {user_name}! 🙏</h2>
                    <p>Aapke liye ek naya update aaya hai:</p>
                    <div style="background: #f4f4f4; padding: 15px; border-left: 5px solid #172554; margin: 20px 0;">
                        <strong style="font-size: 16px;">{job_title}</strong>
                    </div>
                    <p>Iski poori jankari aur apply karne ke liye niche diye button par click karein:</p>
                    <a href="{job_link}" target="_blank" style="display: inline-block; padding: 12px 25px; background-color: #172554; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Check Details Now 🚀</a>
                    <br><br>
                    <p style="font-size: 12px; color: #777;">Best of Luck,<br>
                    <strong>Rahul Raj</strong><br>
                    Rozgar AI - R YADAV PRODUCTION</p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))

        # SMTP Server Setup
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False
