#!/usr/bin/env python3

import awsgi
import connexion

from openapi_server import encoder
from flask_cors import CORS
#from json import JSONEncoder

app = connexion.FlaskApp(__name__, specification_dir='./openapi/')
app.add_api('openapi.yaml',
            arguments={'title': 'The Modern Groom API'},
            pythonic_params=True)
app.app.json_encoder = encoder.CustomJSONEncoder
CORS(app.app)

def handler(event, context):
    return awsgi.response(app, event, context)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8080)
