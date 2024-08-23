import os
from flask import request
import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths

from server.version import get_version


powerlogger = Logger(name="%(name)s", log_record_order=["timestamp", "level", "message"], timestamp="%(created)f")


def log_shopify_id_middleware():
    shopify_id = request.args.get("logged_in_customer_id", "")
    powerlogger.append_keys(shopify_id=shopify_id)


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
