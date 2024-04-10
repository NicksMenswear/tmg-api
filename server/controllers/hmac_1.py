import hashlib
import hmac
import os

from flask import current_app, request

secret_key = os.getenv("client_secret", "")
secret_key = secret_key.encode("utf-8")


def hmac_verification():
    """HMAC verification authorizes all API calls by calculating and matching tokens received from Shopify with those created on the server side."""

    def decorator(func):
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

            is_in_testing_mode = current_app.config.get("TESTING")

            if is_in_testing_mode or hmac.compare_digest(signature, calculated_signature):
                # Remove the HMAC parameters from the kwargs
                for param in ("logged_in_customer_id", "shop", "path_prefix", "timestamp", "signature"):
                    kwargs.pop(param, None)
                return func(*args, **kwargs)
            else:
                return "Unauthorized user!", 401

        return wrapper

    return decorator
