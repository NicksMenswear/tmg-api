#!/usr/bin/env python3
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
from server.logs import (
    append_log_request_context_middleware,
    append_log_response_context_middleware,
    log_request_middleware,
    log_response_middleware,
)
from server.services.activity_service import FakeActivityService, ActivityService
from server.services.attendee_service import AttendeeService
from server.services.audit_service import AuditLogService
from server.services.discount_service import DiscountService
from server.services.email_service import EmailService, FakeEmailService
from server.services.event_service import EventService
from server.services.integrations.activecampaign_service import ActiveCampaignService, FakeActiveCampaignService
from server.services.integrations.aws_service import AWSService, FakeAWSService
from server.services.integrations.shiphero_service import ShipHeroService, FakeShipHeroService
from server.services.integrations.shopify_service import ShopifyService, FakeShopifyService
from server.services.integrations.superblocks_service import SuperblocksService, FakeSuperblocksService
from server.services.look_service import LookService
from server.services.measurement_service import MeasurementService
from server.services.order_service import OrderService
from server.services.product_service import ProductService
from server.services.role_service import RoleService
from server.services.shipping_service import ShippingService
from server.services.size_service import SizeService
from server.services.sku_builder_service import SkuBuilder
from server.services.suit_builder_service import SuitBuilderService
from server.services.user_service import UserService
from server.services.webhook_handlers.shopify_cart_webhook_handler import ShopifyWebhookCartHandler
from server.services.webhook_handlers.shopify_checkout_webhook_handler import ShopifyWebhookCheckoutHandler
from server.services.webhook_handlers.shopify_order_webhook_handler import ShopifyWebhookOrderHandler
from server.services.webhook_handlers.shopify_user_webhook_handler import ShopifyWebhookUserHandler
from server.services.webhook_service import WebhookService
from server.services.workers.e2e_ac_clean_up_worker import E2EActiveCampaignCleanUpWorker
from server.services.workers.e2e_clean_up_worker import E2ECleanUpWorker
from server.version import get_version


def init_sentry():
    def filter_transactions(event, hint):
        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path == "/health":
            return None

        return event

    def before_send(event, hint):
        environment = os.getenv("STAGE")
        fingerprint = event.get("fingerprint", ["{{ default }}"])
        fingerprint.append(environment)
        event["fingerprint"] = fingerprint
        return event

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
        before_send=before_send,
        release=get_version(),
    )
    for logger in ["connexion.decorators.validation"]:
        ignore_logger(logger)


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

    if not run_in_test_mode:
        AuditLogService.init_audit_logging()

    init_services(api.app, run_in_test_mode)

    # Do not reorder, this is ensuring requests are logged with the attributes
    api.app.before_request(append_log_request_context_middleware)
    api.app.before_request(log_request_middleware)
    api.app.after_request(log_response_middleware)
    api.app.after_request(append_log_response_context_middleware)

    return api


def init_services(app, is_testing=False):
    app.stage = os.getenv("STAGE", "dev")
    app.online_store_sales_channel_id = os.getenv(
        "online_store_sales_channel_id", "gid://shopify/Publication/94480072835"
    )
    app.online_store_shop_id = os.getenv("online_store_shop_id", "56965365891")
    app.audit_log_sqs_queue_url = os.getenv("AUDIT_QUEUE_URL", "https://sqs.us-west-2.amazonaws.com/123456789012/audit")
    app.aws_service = FakeAWSService() if is_testing else AWSService()
    app.shopify_service = FakeShopifyService() if is_testing else ShopifyService()
    app.superblocks_service = FakeSuperblocksService() if is_testing else SuperblocksService()
    app.email_service = FakeEmailService() if is_testing else EmailService(app.shopify_service)
    app.activecampaign_service = ActiveCampaignService() if app.stage == "prd" else FakeActiveCampaignService()
    app.activity_service = FakeActivityService() if is_testing else ActivityService()
    app.user_service = UserService(app.shopify_service, app.email_service, app.activecampaign_service)
    app.role_service = RoleService()
    app.look_service = LookService(app.user_service, app.aws_service, app.shopify_service)
    app.attendee_service = AttendeeService(
        app.shopify_service, app.user_service, app.look_service, app.email_service, app.activecampaign_service
    )
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
        app.activecampaign_service,
        app.email_service,
    )
    app.shopify_webhook_user_handler = ShopifyWebhookUserHandler(app.user_service, app.activecampaign_service)
    app.shopify_webhook_cart_handler = ShopifyWebhookCartHandler()
    app.shopify_webhook_checkout_handler = ShopifyWebhookCheckoutHandler()
    app.shipping_service = ShippingService(
        look_service=app.look_service,
        attendee_service=app.attendee_service,
        event_service=app.event_service,
    )
    app.e2e_cleanup_worker = E2ECleanUpWorker(shopify_service=app.shopify_service)
    app.e2e_ac_cleanup_worker = E2EActiveCampaignCleanUpWorker(active_campaign_service=app.activecampaign_service)
    app.suit_builder_service = SuitBuilderService(shopify_service=app.shopify_service, aws_service=app.aws_service)


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
