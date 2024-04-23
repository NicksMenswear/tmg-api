import email
import imaplib
from datetime import datetime
from email import policy
from time import time, sleep

IMAP_HOST = "outlook.office365.com"
IMAP_PORT = 993
EMAIL_ACCOUNT_USERNAME = "e2etmg@hotmail.com"
EMAIL_ACCOUNT_PASSWORD = "fbb06fc8-fd64-11ee-8a70-d73cbe5bfd61"


def look_for_email(subject, email_from, email_to, timeout_seconds=120):
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT_USERNAME, EMAIL_ACCOUNT_PASSWORD)

    timeout = time() + timeout_seconds
    found_email_body = False

    while time() < timeout and not found_email_body:
        found_email_body = search_emails(mail, subject, email_from, email_to)

        if not found_email_body:
            print("Waiting 5 seconds to check again...")
            sleep(5)
        else:
            mail.logout()
            return found_email_body

    mail.logout()


def search_emails(mail, subject, email_from, email_to):
    mail.select("inbox")

    formatted_date = datetime.fromtimestamp(time() - 300).strftime("%d-%b-%Y")
    result, data = mail.uid("search", None, f'(SINCE "{formatted_date}")')

    if result == "OK":
        for num in data[0].split():
            result, data = mail.uid("fetch", num, "(RFC822)")
            if result == "OK":
                msg = email.message_from_bytes(data[0][1], policy=policy.default)

                if (
                    msg["subject"] == subject
                    and (email_from is None or msg["from"] == email_from)
                    and msg["to"] == email_to
                ):
                    return get_email_body(msg)

    return None


def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload()
            elif content_type == "text/html" and "attachment" not in content_disposition:
                return part.get_payload()
    else:
        content_type = msg.get_content_type()

        if content_type == "text/plain" or content_type == "text/html":
            return msg.get_payload()

    return ""
