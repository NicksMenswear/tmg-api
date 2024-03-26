#!/usr/bin/env python3

import connexion

from openapi_server import encoder
# from json import JSONEncoder


def main():
    app = connexion.App(__name__, specification_dir='./openapi/')
    # app.app.json_encoder = encoder.JSONEncoder
    app.app.json_encoder = encoder.CustomJSONEncoder
    app.add_api('openapi.yaml',
                arguments={'title': 'The Modern Groom API'},
                pythonic_params=True,strict_validation=True)

    app.run(host="0.0.0.0",port=8081)


if __name__ == '__main__':
    main()
