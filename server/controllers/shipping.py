import logging

from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


def shipping_price(payload):
    shipping_service = FlaskApp.current().shipping_service

    rate = shipping_service.calculate_shipping_price(payload)

    service_name = "Ground" if rate == "0" else "Expedited"

    return {
        "rates": [
            {
                "service_name": service_name,
                "service_code": "TMG",
                "total_price": rate,
                "currency": "USD",
            }
        ]
    }, 200
