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
    powerlogger.append_keys(versio=get_version() or "")
    powerlogger.append_keys(environment=os.getenv("STAGE"))

    # Override root handler
    for existing_logger in logging.root.manager.loggerDict.values():
        if isinstance(existing_logger, logging.Logger):
            for handler in logger.handlers:
                logger.removeHandler(handler)
            existing_logger.handlers = powerlogger.handlers
            existing_logger.setLevel(powerlogger.log_level)

    # Tune libraries log levels
    for name, logger in logging.root.manager.loggerDict.items():
        for mute in ["connexion.", "flask_cors.", "aws_lambda_powertools.", "sqlalchemy."]:
            if name.startswith(mute) and isinstance(logger, logging.Logger):
                logger.setLevel(logging.INFO)
