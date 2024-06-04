import random
import string


def generate_unique_string(min_length: int = 5, max_length: int = 10) -> str:
    length = random.randint(min_length, max_length)

    return "".join(random.choices(string.ascii_lowercase, k=length))


def generate_unique_name(min_length: int = 5, max_length: int = 10) -> str:
    name = generate_unique_string(min_length, max_length)

    return name.capitalize()


def generate_event_name(min_length: int = 5, max_length: int = 10) -> str:
    return f"Test Event {generate_unique_string(min_length, max_length)}"


def generate_unique_email() -> str:
    name = generate_unique_string()
    host = generate_unique_string()

    return f"{name}@{host}.com"
