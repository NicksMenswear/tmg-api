import re
import uuid


def rnd_str(length: int = 12):
    return str(uuid.uuid4()).replace("-", "")[:length]


def link_from_email(email_body: str):
    pattern = r'<a href="([^"]+)">Click Me</a>'
    match = re.search(pattern, email_body, re.IGNORECASE)

    if match:
        return match.group(1)

    return None
