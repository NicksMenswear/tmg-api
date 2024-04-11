#!/usr/bin/env python3
import logging
import os
from urllib.parse import urlparse

import connexion
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from server import encoder
from server.services.emails import EmailService, FakeEmailService
from server.services.shopify import ShopifyService, FakeShopifyService


def init_sentry():
    def filter_transactions(event, hint):
        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path == "/health":
            return None

        return event

    sentry_sdk.init(
        dsn="https://8e6bac4bea5b3bf97a544417ca20e275@o4507018035724288.ingest.us.sentry.io/4507018177609728",
        integrations=[AwsLambdaIntegration(timeout_warning=True)],
        enable_tracing=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        # Ignoring healthcheck transactions
        before_send_transaction=filter_transactions,
        environment=os.getenv("STAGE"),
    )


def init_logging(debug=False):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(asctime)s %(message)s", level=level)


def init_app(swagger=False):
    options = {"swagger_ui": False}

    if swagger:
        options.update({"swagger_ui": True, "swagger_ui_config": {"url": "/openapi.yaml"}})

    app = connexion.FlaskApp(__name__, specification_dir="./openapi/", options=options)

    app.add_api(
        "openapi.yaml", arguments={"title": "The Modern Groom API"}, pythonic_params=True, strict_validation=True
    )

    app.app.config["TESTING"] = str(os.getenv("TMG_APP_TESTING", False)).lower() == "true"

    app.app.shopify_service = FakeShopifyService() if app.app.config["TESTING"] else ShopifyService()
    app.app.email_service = FakeEmailService() if app.app.config["TESTING"] else EmailService()

    app.app.json_encoder = encoder.CustomJSONEncoder

    return app


def reset_db():
    from server.database.models import Base
    from server.database.database_manager import engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
