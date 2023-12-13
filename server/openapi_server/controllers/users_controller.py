import connexion
import six

from openapi_server.database.models import User  # noqa: E501
from openapi_server import util


def create_user(user=None):  # noqa: E501
    """Create user

     # noqa: E501

    :param user: 
    :type user: dict | bytes

    :rtype: None
    """
    # if connexion.request.is_json:
    #     user = User.from_dict(connexion.request.get_json())  # noqa: E501
    # return 'do some magic!'
    request = connexion.request
    print("request data: ", request.json)
    return "Success"


def get_user_by_id(user_id):  # noqa: E501
    """Get a single user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to retrieve
    :type user_id: int

    :rtype: User
    """
    return 'do some magic!'


def list_users():  # noqa: E501
    """Lists all users

     # noqa: E501


    :rtype: List[User]
    """
    return 'do some magic!'


def update_user(user_id, user):  # noqa: E501
    """Update a user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to update
    :type user_id: int
    :param user: 
    :type user: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        user = User.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
