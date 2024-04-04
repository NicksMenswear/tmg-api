#!/usr/bin/env python3
import os

import connexion
import logging

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from server import encoder


def init_sentry():
    sentry_sdk.init(
        dsn="https://8e6bac4bea5b3bf97a544417ca20e275@o4507018035724288.ingest.us.sentry.io/4507018177609728",
        integrations=[AwsLambdaIntegration(timeout_warning=True)],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        enable_tracing=True,
        environment=os.getenv("STAGE")
    )

def init_logging(debug=False):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(asctime)s %(message)s', level=level)

def init_app(swagger=False):
    options = {"swagger_ui": False}
    if swagger:
        options.update({"swagger_ui": True, 'swagger_ui_config': {'url': '/openapi.yaml'}})
    app = connexion.FlaskApp(
        __name__, 
        specification_dir='./openapi/', 
        options=options
    )
    app.add_api(
        'openapi.yaml',
        arguments={'title': 'The Modern Groom API'},
        pythonic_params=True,
        strict_validation=True
    )
    app.app.json_encoder = encoder.CustomJSONEncoder
    return app

def reset_db():
    from sqlalchemy import create_engine
    from server.database.models import Base
    from server.database.database_manager import DATABASE_URL
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
