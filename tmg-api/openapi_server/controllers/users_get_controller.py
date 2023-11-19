import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.user import User  # noqa: E501
from openapi_server import util


def get_user_by_id(user_id):  # noqa: E501
    """Get a single user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to retrieve
    :type user_id: int

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    return 'do some magic!'
