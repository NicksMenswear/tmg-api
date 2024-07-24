#!/usr/bin/env python3
import logging
import os
import sys
from urllib.parse import urlparse

import connexion
import sentry_sdk
from flask_cors import CORS
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from sentry_sdk.integrations.logging import ignore_logger

from server import encoder
from server.database.database_manager import db, DATABASE_URL
from server.flask_app import FlaskApp
from server.services.activecampaign_service import ActiveCampaignService, FakeActiveCampaignService
from server.services.attendee_service import AttendeeService
from server.services.aws_service import AWSService, FakeAWSService
from server.services.discount_service import DiscountService
from server.services.email_service import EmailService, FakeEmailService
from server.services.event_service import EventService
from server.services.look_service import LookService
from server.services.measurement_service import MeasurementService
from server.services.order_service import OrderService
from server.services.product_service import ProductService
from server.services.role_service import RoleService
from server.services.shiphero_service import ShipHeroService, FakeShipHeroService
from server.services.shopify_service import ShopifyService, FakeShopifyService
from server.services.shopify_webhook_handlers.order_handler import ShopifyWebhookOrderHandler
from server.services.shopify_webhook_handlers.user_handler import ShopifyWebhookUserHandler
from server.services.size_service import SizeService
from server.services.sku_builder_service import SkuBuilder
from server.services.superblocks_service import SuperblocksService, FakeSuperblocksService
from server.services.user_service import UserService
from server.services.webhook_service import WebhookService


def init_sentry():
    def filter_transactions(event, hint):
        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path == "/health":
            return None

        return event

    def get_version():
        try:
            with open("./VERSION") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    sentry_sdk.init(
        dsn="https://8e6bac4bea5b3bf97a544417ca20e275@o4507018035724288.ingest.us.sentry.io/4507018177609728",
        integrations=[AwsLambdaIntegration(timeout_warning=True)],
        enable_tracing=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.1,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.1,
        # Ignoring healthcheck transactions
        before_send_transaction=filter_transactions,
        environment=os.getenv("STAGE"),
        release=get_version(),
    )
    for logger in ["connexion.decorators.validation"]:
        ignore_logger(logger)


def init_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s", level=level, force=True)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict:
        if name.startswith("connexion."):
            logging.getLogger(name).setLevel(logging.INFO)


def init_app(is_testing=False):
    options = {"swagger_ui": False}
    api = connexion.FlaskApp(__name__, specification_dir="./openapi/", options=options)
    CORS(api.app)
    api.add_api(
        "openapi.yaml", arguments={"title": "The Modern Groom API"}, pythonic_params=True, strict_validation=True
    )
    api.app.json_encoder = encoder.CustomJSONEncoder

    run_in_test_mode = is_testing or os.getenv("TMG_APP_TESTING", "false").lower() == "true"

    api.app.config["TMG_APP_TESTING"] = run_in_test_mode

    FlaskApp.set(api.app)

    init_services(api.app, run_in_test_mode)

    return api


def init_services(app, is_testing=False):
    app.stage = os.getenv("STAGE", "dev")
    app.aws_service = FakeAWSService() if is_testing else AWSService()
    app.shopify_service = FakeShopifyService() if is_testing else ShopifyService()
    app.superblocks_service = FakeSuperblocksService() if is_testing else SuperblocksService()
    app.email_service = FakeEmailService() if is_testing else EmailService(app.shopify_service)
    app.activecampaign_service = ActiveCampaignService()  # if app.stage == "prd" else FakeActiveCampaignService()
    app.user_service = UserService(app.shopify_service, app.email_service)
    app.role_service = RoleService()
    app.look_service = LookService(app.user_service, app.aws_service, app.shopify_service)
    app.attendee_service = AttendeeService(app.shopify_service, app.user_service, app.email_service)
    app.sku_builder = SkuBuilder()
    app.event_service = EventService(
        attendee_service=app.attendee_service, role_service=app.role_service, look_service=app.look_service
    )
    app.discount_service = DiscountService(
        app.shopify_service, app.user_service, app.event_service, app.attendee_service, app.look_service
    )
    app.measurement_service = MeasurementService()
    app.product_service = ProductService()
    app.order_service = OrderService(
        user_service=app.user_service,
        product_service=app.product_service,
        measurement_service=app.measurement_service,
        sku_builder=app.sku_builder,
    )
    app.size_service = SizeService(app.user_service, app.measurement_service, order_service=app.order_service)
    app.webhook_service = WebhookService()
    app.online_store_sales_channel_id = app.shopify_service.get_online_store_sales_channel_id()
    app.online_store_shop_id = app.shopify_service.get_online_store_shop_id()
    app.images_data_endpoint_host = f"data.{app.stage if app.stage == 'prd' else 'dev'}.tmgcorp.net"
    app.shiphero_service = FakeShipHeroService() if is_testing else ShipHeroService()
    app.shopify_webhook_order_handler = ShopifyWebhookOrderHandler(
        app.shopify_service,
        app.discount_service,
        app.user_service,
        app.attendee_service,
        app.look_service,
        app.size_service,
        app.measurement_service,
        app.order_service,
        app.product_service,
        app.sku_builder,
        app.event_service,
        app.shiphero_service,
    )
    app.shopify_webhook_user_handler = ShopifyWebhookUserHandler(app.user_service)


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
