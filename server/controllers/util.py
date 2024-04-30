import hashlib
import hmac
import os
from functools import wraps

import urllib3
from flask import request

from server.flask_app import FlaskApp

secret_key = os.getenv("client_secret", "")
secret_key = secret_key.encode("utf-8")

http_pool = urllib3.PoolManager()


def hmac_verification(func):
    """HMAC verification authorizes all API calls by calculating and matching tokens received from Shopify with those created on the server side."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Creating a decorator wrapper function for HMAC verification that accepts *kwargs from the API endpoint."""
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

        is_in_testing_mode = FlaskApp.current().config.get("TMG_APP_TESTING")

        if is_in_testing_mode or hmac.compare_digest(signature, calculated_signature):
            # Remove the HMAC parameters from the kwargs
            for param in ("logged_in_customer_id", "shop", "path_prefix", "timestamp", "signature"):
                kwargs.pop(param, None)
            return func(*args, **kwargs)
        else:
            return "Unauthorized user!", 401

    return wrapper


def http(method, *args, **kwargs):
    merge_kwargs = {
        "timeout": 3,
        "retries": urllib3.util.Retry(total=2, connect=None, read=None, redirect=0, status=None),
    }
    merge_kwargs.update(kwargs)
    if method == "POST":
        http_pool = urllib3.PoolManager()  # Avoid caching connections for POST, use new pool every time.
    return http_pool.request(method, *args, **merge_kwargs)
