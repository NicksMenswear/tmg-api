import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from openapi_server.database.models import User
from openapi_server.database.database_manager import get_database_session
import uuid
from werkzeug.exceptions import HTTPException


def create_user(user_data):  # noqa: E501
    """Create user

    :param user_data:
    :type user_data: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """ # noqa: E501
    try:
        db = get_database_session()
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            shopify_id=user_data['shopify_id']
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return 'User created successfully!', 201
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
