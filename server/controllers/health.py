import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from server.controllers.util import http
from server.database.models import ProductItem
from server.flask_app import FlaskApp


logger = logging.getLogger(__name__)

TOP_SITES = [
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.apple.com",
]


def health2():
    return health()


def health():
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            checks = (executor.submit(check) for check in (_check_db_connection, _check_external_connection))
            for future in as_completed(checks):
                future.result()
    except Exception as e:
        logger.exception(e)
        return f"Internal Server Error: {e}", 500

    return "OK", 200


def _check_db_connection():
    with FlaskApp.app_context():
        ProductItem.query.first()


def _check_external_connection():
    num_successful_requests = 0

    with ThreadPoolExecutor(max_workers=len(TOP_SITES)) as executor:
        futures = (executor.submit(_site_available, url) for url in TOP_SITES)

        for future in as_completed(futures):
            if future.result():
                num_successful_requests += 1

    if num_successful_requests < len(TOP_SITES) - 1:
        raise Exception("Failed to connect to more then one of the top sites.")


def _site_available(url):
    try:
        response = http("HEAD", url)
        return 200 <= response.status < 400
    except Exception as e:
        logger.warning(f"Failed to connect to {url}: {e}")
        return False
