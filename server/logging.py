import json
from functools import wraps
from flask import request
import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.database.models import User

logger = Logger(name="%(name)s")


def log_shopify_id_middleware():
    shopify_id = request.args.get("logged_in_customer_id")
    if shopify_id:
        logger.append_keys(shopify_id=shopify_id)
    else:
        logger.append_keys(shopify_id="")


def init_logging(service, debug=False):
    logger.append_keys(service=service)

    # Override root handler
    logging.root.handlers = logger.handlers
    logging.root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Tune libraries log levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict:
        if name.startswith("connexion."):
            logging.getLogger(name).setLevel(logging.INFO)
