import re
import uuid


def rnd_str(length: int = 12):
    return str(uuid.uuid4()).replace("-", "")[:length]


def link_from_email(email_body: str, link_text: str = "Click Me"):
    pattern = r'<a href="([^"]+)">' + link_text + "</a>"
    match = re.search(pattern, email_body, re.IGNORECASE)

    if match:
        return match.group(1)

    return None
