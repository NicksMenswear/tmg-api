import connexion
import six
from openapi_server.database.models import User
from openapi_server.database.database_manager import get_database_session
from werkzeug.exceptions import HTTPException


db = get_database_session()


def get_user_by_id(email):  # noqa: E501
    """Get a single user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to retrieve
    :type user_id: int

    :rtype: User
    """
    try:
        user = db.query(User).filter(User.email==email).first()
        formatted_user = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'shopify_id': user.shopify_id
        }
        return formatted_user
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
