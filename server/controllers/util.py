import base64
import hashlib
import hmac
import logging
import os
from functools import wraps
from copy import deepcopy
import logging

import urllib3
from flask import request, abort

logger = logging.getLogger(__name__)


from server.flask_app import FlaskApp

secret_key = os.getenv("client_secret", "")
secret_key = secret_key.encode("utf-8")
webhook_signature_key = os.getenv("webhook_signature_key")

http_pool = urllib3.PoolManager()
logger = logging.getLogger(__name__)


def hmac_verification(func):
    """HMAC verification authorizes all API calls by calculating and matching tokens received from Shopify with those created on the server side."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        signature = request.args.get("signature", "")
        query_params = request.args.copy()
        query_params.pop("signature", None)
        sorted_params = "".join(
            [
                f"{key}={','.join(value) if isinstance(value, list) else value}"
                for key, value in sorted(query_params.items())
            ]
        )

        calculated_signature = hmac.new(secret_key, sorted_params.encode("utf-8"), hashlib.sha256).hexdigest()

        is_in_testing_mode = FlaskApp.current().config.get("TMG_APP_TESTING", False)

        if is_in_testing_mode or hmac.compare_digest(signature, calculated_signature):
            # Remove the HMAC parameters from the kwargs
            for param in ("logged_in_customer_id", "shop", "path_prefix", "timestamp", "signature"):
                kwargs.pop(param, None)

            if is_in_testing_mode:
                logger.debug("HMAC webhook verification succeeded: in testing mode.")
            else:
                logger.debug("HMAC webhook verification succeeded: signature matched.")

            return func(*args, **kwargs)
        else:
            logger.debug("hmac verification failed: signature mismatch.")
            return "Unauthorized user!", 401

    return wrapper


def hmac_webhook_verification(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        is_in_testing_mode = FlaskApp.current().config.get("TMG_APP_TESTING", False)

        if is_in_testing_mode:
            logger.debug("HMAC webhook verification succeeded: in testing mode.")
            return func(*args, **kwargs)

        received_hmac = request.headers.get("X-Shopify-Hmac-SHA256")

        if not received_hmac:
            logger.debug("HMAC webhook verification failed: missing 'X-Shopify-Hmac-SHA256' header.")
            abort(403)

        request_data = request.get_data()

        if not request_data:
            logger.debug("HMAC webhook verification failed: missing 'X-Shopify-Hmac-SHA256' header.")
            abort(403)

        hash = hmac.new(webhook_signature_key.encode("utf-8"), request_data, hashlib.sha256)
        calculated_hmac = base64.b64encode(hash.digest()).decode("utf-8")

        if not hmac.compare_digest(calculated_hmac, received_hmac):
            logger.debug("HMAC webhook verification failed: signature mismatch.")
            abort(403)

        logger.debug("HMAC webhook verification succeeded: signature matched.")

        return func(*args, **kwargs)

    return wrapper


def token_verification(func, api_token=os.getenv("API_TOKEN", None)):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request_token = request.headers.get("X-Api-Access-Token", "unset")
        if request_token == api_token:
            return func(*args, **kwargs)
        else:
            logger.debug("API token verification failed: token mismatch.")
            abort(403)

    return wrapper


def http(method, *args, **kwargs):
    merge_kwargs = {
        "timeout": 3,
        "retries": urllib3.util.Retry(total=2, connect=None, read=None, redirect=0, status=None),
    }
    merge_kwargs.update(kwargs)
    _log_request(method, *args, **merge_kwargs)
    if method == "POST":
        # Avoid caching connections for POST, use new pool every time.
        response = urllib3.PoolManager().request(method, *args, **merge_kwargs)
    else:
        response = http_pool.request(method, *args, **merge_kwargs)
    _log_response(response)
    return response


def _log_request(method, *args, **kwargs):
    log_kwargs = deepcopy(kwargs)
    log_kwargs.get("headers", {})["X-Shopify-Access-Token"] = "***"
    logger.debug(f"Making {method} request with args {args} {log_kwargs}")


def _log_response(response):
    logger.debug(f"Received response {response.status} with data {response.data}")
