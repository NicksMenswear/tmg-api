import connexion
import six

from openapi_server.models.order import Order  # noqa: E501
from openapi_server import util


def get_order_by_id(order_id):  # noqa: E501
    """Retrieve a specific order by ID

     # noqa: E501

    :param order_id: Unique identifier of the order to retrieve
    :type order_id: int

    :rtype: Order
    """
    return 'do some magic!'
