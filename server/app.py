#!/usr/bin/env python3

import connexion
import logging

from server import encoder


def init_logging():
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format='%(asctime)s %(message)s',level=logging.DEBUG)

def init_app():
    options = {'swagger_ui_config': {'url': '/openapi.yaml'}}
    app = connexion.FlaskApp(__name__, specification_dir='./openapi/', options=options)
    app.add_api('openapi.yaml',
                arguments={'title': 'The Modern Groom API'},
                pythonic_params=True)
    app.app.json_encoder = encoder.CustomJSONEncoder
    return app

def reset_db():
    from sqlalchemy import create_engine
    from server.database.models import Base
    from server.database.database_manager import DATABASE_URL
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    