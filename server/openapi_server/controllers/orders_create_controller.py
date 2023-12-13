import connexion
import six

from openapi_server.models.order import Order  # noqa: E501
from openapi_server import util


def create_order(order):  # noqa: E501
    """Create order

     # noqa: E501

    :param order: 
    :type order: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        order = Order.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
