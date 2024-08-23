import logging

from connexion import request

logger = logging.getLogger(__name__)


def shipping(payload):
    logger.info(payload)
    logger.info(request.headers)
    logger.info(request.get_data())
    return {
        "rates": [
            {
                "service_name": "zinovii-overnight",
                "service_code": "ON",
                "total_price": "4500",
                "description": "This is the fastest option by far",
                "currency": "USD",
                "min_delivery_date": "2024-08-28 14:48:45 -0400",
                "max_delivery_date": "2024-08-30 14:48:45 -0400",
            }
        ]
    }, 200
