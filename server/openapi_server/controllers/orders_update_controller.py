import connexion
import six

from openapi_server.models.order import Order  # noqa: E501
from openapi_server import util


def update_order(order_id, order):  # noqa: E501
    """Update an existing order by ID

     # noqa: E501

    :param order_id: Unique identifier of the order to update
    :type order_id: int
    :param order: 
    :type order: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        order = Order.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
