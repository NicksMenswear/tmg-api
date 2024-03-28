import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, body, sender_email, receiver_email, password):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        html_body = f"""\
        <html>
          <body>
            <p>{body}</p>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender_email, password)
            smtp_server.sendmail(sender_email, receiver_email, msg.as_string())
            print('Message sent successfully.')

    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")


