import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.user import User  # noqa: E501
from openapi_server import util


def create_user(user):  # noqa: E501
    """Create user

     # noqa: E501

    :param user: 
    :type user: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        user = User.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_by_id(user_id):  # noqa: E501
    """Get a single user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to retrieve
    :type user_id: int

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    return 'do some magic!'


def list_users():  # noqa: E501
    """Lists all users

     # noqa: E501


    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    return 'do some magic!'


def update_user(user_id, user):  # noqa: E501
    """Update a user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to update
    :type user_id: int
    :param user: 
    :type user: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        user = User.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
