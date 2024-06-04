import re
import string
import random


def generate_unique_string(min_length: int = 5, max_length: int = 10) -> str:
    length = random.randint(min_length, max_length)

    return "".join(random.choices(string.ascii_lowercase, k=length))


def generate_unique_name(min_length: int = 5, max_length: int = 10) -> str:
    name = generate_unique_string(min_length, max_length)

    return name.capitalize()


def generate_unique_email() -> str:
    name = generate_unique_string()
    host = generate_unique_string()

    return f"{name}@{host}.com"


def unique_event_name():
    return f"Event-{generate_unique_string(10, 15)}"


def link_from_email(email_body: str, link_text: str = "Click Me"):
    pattern = r'<a href="([^"]+)">' + link_text + "</a>"
    match = re.search(pattern, email_body, re.IGNORECASE)

    if match:
        return match.group(1)

    return None
