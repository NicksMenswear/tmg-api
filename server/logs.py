import os
from flask import request
import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths

from server.version import get_version


powerlogger = Logger(name="%(name)s")


def log_shopify_id_middleware():
    shopify_id = request.args.get("logged_in_customer_id", "")
    powerlogger.append_keys(shopify_id=shopify_id)


def init_logging(service, debug=False):
    powerlogger.setLevel(logging.DEBUG if debug else logging.INFO)
    powerlogger.append_keys(service=service)
    powerlogger.append_keys(version=get_version() or "")
    powerlogger.append_keys(environment=os.getenv("STAGE"))

    # Clean root handler (AWS lambda hack)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Subscribe to all library loggers
    for existing_logger in logging.root.manager.loggerDict.values():
        if isinstance(existing_logger, logging.Logger):
            existing_logger.handlers = powerlogger.handlers
            existing_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Mute noisy library log levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict:
        for mute in ["sqlalchemy.orm.", "connexion.", "flask_cors.", "botocore", "boto3"]:
            if name.startswith(mute):
                logging.getLogger(name).setLevel(logging.WARNING)
