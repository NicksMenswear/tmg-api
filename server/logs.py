import os
from flask import request
import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.version import get_version
from server.database.models import User

logger = Logger(name="%(name)s")


def log_shopify_id_middleware():
    shopify_id = request.args.get("logged_in_customer_id", "")
    logger.append_keys(shopify_id=shopify_id)


def init_logging(service, debug=False):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.append_keys(service=service)
    logger.append_keys(release=get_version() or "")
    logger.append_keys(environment=os.getenv("STAGE"))

    # Override root handler
    for existing_logger in logging.root.manager.loggerDict.values():
        if isinstance(existing_logger, logging.Logger):
            existing_logger.handlers = logger.handlers
            existing_logger.setLevel(logger.log_level)

    # Tune libraries log levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict:
        if name.startswith("connexion."):
            logging.getLogger(name).setLevel(logging.INFO)
