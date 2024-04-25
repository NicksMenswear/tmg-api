#!/usr/bin/env python3
import logging
import os
import sys
from urllib.parse import urlparse

import connexion
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from server import encoder
from server.database.database_manager import db, DATABASE_URL
from server.flask_app import FlaskApp
from server.services.emails import FakeEmailService, EmailService
from server.services.shopify import FakeShopifyService, ShopifyService


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
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s", level=level, force=True)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict:
        if name.startswith("connexion."):
            logging.getLogger(name).setLevel(logging.INFO)


def init_app():
    options = {"swagger_ui": False}
    api = connexion.FlaskApp(__name__, specification_dir="./openapi/", options=options)
    api.add_api(
        "openapi.yaml", arguments={"title": "The Modern Groom API"}, pythonic_params=True, strict_validation=True
    )
    api.app.json_encoder = encoder.CustomJSONEncoder
    FlaskApp.set(api.app)
    current_app = FlaskApp.current()
    current_app.config["TMG_APP_TESTING"] = os.getenv("TMG_APP_TESTING", "false").lower() == "true"

    current_app.shopify_service = (
        ShopifyService() if not current_app.config["TMG_APP_TESTING"] else FakeShopifyService()
    )
    current_app.email_service = EmailService() if not current_app.config["TMG_APP_TESTING"] else FakeEmailService()

    return api


def init_db():
    app = FlaskApp.current()
    with app.app_context():
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
        app.config["SQLALCHEMY_ECHO"] = False
        db.init_app(app)

        print("Connecting to database...")
        with db.engine.connect():
            print("Database connected successfully.")


def lambda_teardown(signum, frame):
    print("SIGTERM received.")
    app = FlaskApp.current()
    with app.app_context():
        print("Closing DB session...")
        db.session.remove()
        print("Terminating DB connections...")
        db.engine.dispose()
    print("Cleanup complete. Exiting.")
    sys.exit(0)
