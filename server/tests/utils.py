import random
import string

from server.database.models import SuitBuilderItemType


def generate_unique_string(min_length: int = 5, max_length: int = 10) -> str:
    random.seed()
    length = random.randint(min_length, max_length)

    return "".join(random.choices(string.ascii_lowercase, k=length))


def generate_unique_name(min_length: int = 5, max_length: int = 10) -> str:
    name = generate_unique_string(min_length, max_length)

    return name.capitalize()


def generate_event_name(min_length: int = 5, max_length: int = 10) -> str:
    return f"Test Event {generate_unique_string(min_length, max_length)}"


def generate_phone_number() -> str:
    return f"+1{random.randint(1000000000, 9999999999)}"


def generate_email() -> str:
    rnd = generate_unique_string()
    return f"e2e+{rnd}@mail.dev.tmgcorp.net"


def generate_look_name() -> str:
    return f"Test Look {generate_unique_string().capitalize()}"


def generate_product_sku() -> str:
    colors = {"BLK", "CHA", "HDN", "LTG", "TAN", "MDT"}
    random_color = random.choice(list(colors))

    return f"{random.randint(0, 9)}01A{random.randint(1, 5)}{random_color}"


def generate_product_type() -> str:
    types = list(SuitBuilderItemType)

    return random.choice(types).value
