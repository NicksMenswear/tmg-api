import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from server.controllers.shopify import get_activation_url
from server.services import ServiceError


class FakeEmailService:
    def send_activation_url(self, email, shopify_customer_id):
        pass


class EmailService:
    def __init__(self):
        self.sender_password = os.getenv("sender_password")
        self.sender_email = os.getenv("sender_email")

    @staticmethod
    def send_email(subject, body, sender_email, receiver_email, password):
        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject

            html_body = f"""\
            <html>
              <body>
                <p>{body}</p>
              </body>
            </html>
            """

            msg.attach(MIMEText(html_body, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5) as smtp_server:
                smtp_server.login(sender_email, password)
                smtp_server.sendmail(
                    sender_email,
                    receiver_email,
                    msg.as_string(),
                )
                print("Message sent successfully.")
        except Exception as e:
            raise ServiceError("Failed to send email.", e)

    def send_activation_url(self, email, shopify_customer_id):
        activation_url = get_activation_url(shopify_customer_id)
        activation_link = f'<a href="{activation_url}">Click Me</a>'
        body = f"Click the following link to activate your account: {activation_link}"

        self.send_email("Registration email", body, self.sender_email, email, self.sender_password)
