import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from openapi_server.database.database_manager import get_database_session


def create_user(username):  # noqa: E501
    """Create user

     # noqa: E501

    :param username: 
    :type user: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        user_data = connexion.request.get_json()
        print(user_data)
        session = get_database_session()
        new_user = User(name=user_data.get('username'), email=user_data.get('email'))
        # Add the new user to the database session and commit
        session.add(new_user)
        session.commit()
        return 'User created successfully!', 201
