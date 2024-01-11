#!/usr/bin/env python3

import awsgi
import connexion
import logging

from openapi_server import encoder

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)


app = connexion.FlaskApp(__name__, specification_dir='./openapi/')
app.add_api('openapi.yaml',
            arguments={'title': 'The Modern Groom API'},
            pythonic_params=True)
app.app.json_encoder = encoder.CustomJSONEncoder

def lambda_handler(event, context):
    return awsgi.response(app, event, context)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8080)
