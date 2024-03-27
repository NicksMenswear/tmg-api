#!/usr/bin/env python3

import awsgi
import connexion
import logging

import encoder

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.DEBUG)

options = {'swagger_ui_config': {'url': '/openapi.yaml'}}
app = connexion.FlaskApp(__name__, specification_dir='./openapi/', options=options)
app.add_api('openapi.yaml',
            arguments={'title': 'The Modern Groom API'},
            pythonic_params=True)
app.app.json_encoder = encoder.CustomJSONEncoder

def lambda_handler(event, context):
    return awsgi.response(app, event, context)

def _init_db():
    from sqlalchemy import create_engine
    from database.models import Base
    from database.database_manager import DATABASE_URL
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine) 

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
    