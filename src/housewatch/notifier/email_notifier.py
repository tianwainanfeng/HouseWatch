# src/housewatch/notifier/email_notifier.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from housewatch.models.house import House


class EmailNotifier:
    """Send email notifications for new house matches"""

    def __init__(self, email_config: dict):
        self.config = email_config
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.sender_email = self.config.get("sender_email", "")
        self.sender_password = self.config.get("sender_password", "")
        self.recipient_email = self.config.get("recipient_email", "")
    

    def send_notification(self, houses: List[House]) -> bool:
        """Send email notification with matching houses"""
        if not houses:
            print("No houses to notify")
            return False
 
        if not self.sender_email or not self.sender_password:
            print("Error: email credentials missing (Check your .env and email.yaml)")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Found {len(houses)} new houses matches!"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Create HTML content
            html_content = self._create_html_content(houses)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # Send email via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(0) # use 1 for debug
                server.starttls() # use TLS security
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Email sent with {len(houses)} founded houses!")
            return True
        
        except Exception as e:
            print(f'❌ Failed to send email: {e}')
            return False


    def _create_html_content(self, houses: List[House]) -> str:
        """Generate HTML email content"""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2c3e50;"> New House Matches Found!</h2>
            <p>Found <strong>{len(houses)}</strong> houses matching the criteria:</p>
            <hr style="border: none; border-top: 1px solid #eee;">
        """

        # count from 1 instead of 0
        for i, house in enumerate(houses, 1):
            html += f"""
            <div style="border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
                <h3 styl"margin-top: 0; color: #e67e22">#{i}: {house.address}</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="width: 120px;"><strong>Price:</strong></td><td>{house.formatted_price}</td></tr>
                    <tr><td><strong>Year Built:</strong></td><td>{house.year_built or 'N/A'}</td></tr>
                    <tr><td><strong>Type:</strong></td><td>{house.property_type}</td></tr>
                    <tr><td><strong>Schools:</strong></td><td>{', '.join(house.schools) if house.schools else 'N/A'}</td></tr>
                </table>
                <p style="margin-top: 15px;">
                    <a href="{house.url}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View on Redfin</a>
                </p>
            </div>
            """

        html += """
            <pstyle="color: #7f8c8d; font-size: 12px; margin-top: 30px;>
            --<br>
            This is an automated message from HouseWatch. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        return html
                

            


