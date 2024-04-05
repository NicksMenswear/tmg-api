from server.database.database_manager import get_database_session
from server.database.models import ProductItem
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

TOP_SITES = [
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.facebook.com",
    "https://www.apple.com",
]


def health():
    try:
        __check_db_connection()
        __check_external_connection()
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error: {e}", 500

    return "OK", 200


def __check_db_connection():
    db = get_database_session()
    db.query(ProductItem).first()


def __check_external_connection():
    num_successful_requests = 0

    with ThreadPoolExecutor(max_workers=len(TOP_SITES)) as executor:
        future_to_url = {executor.submit(__site_available, url): url for url in TOP_SITES}

        for future in as_completed(future_to_url):
            if future.result():
                num_successful_requests += 1

    if num_successful_requests < len(TOP_SITES) - 1:
        raise Exception("Failed to connect to more then one of the top sites.")


def __site_available(url):
    try:
        response = requests.get(url, timeout=5)
        return 200 <= response.status_code < 400
    except requests.RequestException:
        return False
