import connexion
import six
from openapi_server.database.models import User
from openapi_server.database.database_manager import get_database_session
from werkzeug.exceptions import HTTPException


db = get_database_session()


def list_users():  # noqa: E501
    """Lists all users

     # noqa: E501


    :rtype: List[User]
    """
    try:
        formatted_users = []
        users = db.query(User).all()
        for user in users:
            formatted_user = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'shopify_id': user.shopify_id,
                'temp' : user.temp,
                'role' : user.role
            }
            formatted_users.append(formatted_user)
        return formatted_users
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
