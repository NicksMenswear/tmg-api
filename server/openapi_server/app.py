#!/usr/bin/env python3

import awsgi
import connexion
import logging
import encoder


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

init_logging()
app = init_app()

def lambda_handler(event, context):
    return awsgi.response(app, event, context)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
    