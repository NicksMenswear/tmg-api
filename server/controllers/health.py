from flask import current_app as app
from server.database.database_manager import get_database_session
from server.database.models import ProductItem
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib3

TOP_SITES = [
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.netlify.com",
    "https://www.apple.com",
]


def health():
    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            checks = (executor.submit(check) for check in (__check_db_connection, __check_external_connection))
            for future in as_completed(checks):
                future.result()
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
        futures = (executor.submit(__site_available, url) for url in TOP_SITES)

        for future in as_completed(futures):
            if future.result():
                num_successful_requests += 1

    if num_successful_requests < len(TOP_SITES) - 1:
        raise Exception("Failed to connect to more then one of the top sites.")


def __site_available(url):
    try:
        http = urllib3.PoolManager()
        response = http.request("GET", url, timeout=3)
        return 200 <= response.status < 400
    except Exception as e:
        app.logger.error(f"Failed to connect to {url}: {e}")
        return False
