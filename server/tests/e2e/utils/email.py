import email
import imaplib
import re
from datetime import datetime
from email import policy
from time import time, sleep
from urllib.parse import unquote

from server.tests.e2e import IMAP_HOST, IMAP_PORT, EMAIL_ACCOUNT_PASSWORD, EMAIL_ACCOUNT_USERNAME


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
    result, data = mail.select("inbox")
    if result != "OK":
        raise Exception(f"Error selecting inbox: {result}")

    formatted_date = datetime.fromtimestamp(time() - 60 * 60 * 2).strftime("%d-%b-%Y")
    result, data = mail.uid("search", None, f'(SINCE "{formatted_date}")')

    if result == "OK":
        for num in data[0].split():
            result, data = mail.uid("fetch", num, "(RFC822)")
            if result == "OK":
                msg = email.message_from_bytes(data[0][1], policy=policy.default)

                if (
                    msg["subject"] == subject
                    and (email_from is None or email_from in msg["from"])
                    and msg["to"] == email_to
                ):
                    return get_email_body(msg)

    return None


def get_email_body(msg):
    content = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                content = content + part.get_payload(decode=True).decode("utf-8")
            elif content_type == "text/html" and "attachment" not in content_disposition:
                content = content + part.get_payload(decode=True).decode("utf-8")
    else:
        content_type = msg.get_content_type()

        if content_type == "text/plain" or content_type == "text/html":
            content = msg.get_payload(decode=True).decode("utf-8")

    return content


def get_activate_account_link_from_email(email_body: str):
    pattern = r'(https://[^/]+/account/activate/[^"\s]+)'
    match = re.search(pattern, email_body)

    result = None

    if match:
        result = match.group(1)

        if result:
            return result

    pattern = r'https://click\.pstmrk\.it/[a-zA-Z0-9]+/([^"]+%2Faccount%2Factivate%2F[^/]+%2F[^/]+)'
    match = re.search(pattern, email_body)

    if match:
        encoded_url = match.group(1)
        decoded_url = unquote(encoded_url)
        result = f"https://{decoded_url}"

    return result
