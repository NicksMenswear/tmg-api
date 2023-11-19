import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.order import Order  # noqa: E501
from openapi_server import util


def get_order_by_id(order_id):  # noqa: E501
    """Retrieve a specific order by ID

     # noqa: E501

    :param order_id: Unique identifier of the order to retrieve
    :type order_id: int

    :rtype: Union[Order, Tuple[Order, int], Tuple[Order, int, Dict[str, str]]
    """
    return 'do some magic!'
