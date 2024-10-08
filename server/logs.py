import inspect
import json
import logging
import os
from datetime import datetime
from functools import wraps

from aws_lambda_powertools import Logger
from flask import request

from server.version import get_version

powerlogger = Logger(name="%(name)s", log_record_order=["timestamp", "level", "message"], use_rfc3339=True, utc=True)
logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("net.tmgcorp.logging.internal.audit")


def audit_log(type, body):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": type,
        "data": body,
    }
    audit_logger.info(json.dumps(log_entry))


def audit(static=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                exception = None
            except Exception as e:
                result = None
                exception = str(e)
                raise
            finally:
                audit_log(
                    "function_call",
                    {
                        "function": func.__name__,
                        "module": inspect.getmodule(func).__name__,
                        "args": args if static else args[1:],  # Drop self
                        "kwargs": kwargs,
                        "result": result,
                        "exception": exception,
                    },
                )
            return result

        return wrapper

    return decorator


def append_log_request_context_middleware():
    shopify_id = request.args.get("logged_in_customer_id", "")
    powerlogger.append_keys(shopify_id=shopify_id)

    endpoint = request.path
    args = request.args.to_dict()
    method = request.method
    powerlogger.append_keys(
        request={
            "method": method,
            "path": endpoint,
            "args": args,
        },
        response={},
    )


def append_log_response_context_middleware(response):
    code = response.status_code
    powerlogger.append_keys(response={"code": code})
    return response


def log_request_middleware():
    try:
        json_payload = json.loads(request.data)
        redacted_payload = {k: v for k, v in json_payload.items() if k not in ["image"]}
    except Exception:
        redacted_payload = request.data
    logger.debug("API Request: %s %s %s %s", request.method, request.path, request.args.to_dict(), redacted_payload)


def log_response_middleware(response):
    logger.debug("API Response: %s %s", response.status_code, response.data)
    return response


def init_logging(service, debug=False):
    level = logging.DEBUG if debug else logging.INFO
    powerlogger.setLevel(level)
    powerlogger.append_keys(service=service)
    powerlogger.append_keys(version=get_version() or "")
    powerlogger.append_keys(environment=os.getenv("STAGE"))

    # Clean root handler (AWS lambda hack)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Capture all library loggers
    logging.root.handlers = powerlogger.handlers
    for logger in logging.root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(level)

    # Mute noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict:
        for mute in ["sqlalchemy.orm", "connexion", "flask_cors", "aws_lambda_powertools", "botocore", "boto3"]:
            if name.startswith(mute):
                logging.getLogger(name).setLevel(logging.WARNING)
