import connexion
import six
from openapi_server.database.models import User
from openapi_server.database.database_manager import get_database_session
from werkzeug.exceptions import HTTPException


db = get_database_session()


def update_user(user_data):  # noqa: E501
    """Update a user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to update
    :type user_id: int
    :param user: 
    :type user: dict | bytes

    :rtype: None
    """

    try:
        user = db.query(User).filter(User.email == user_data['email']).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.shopify_id = user_data['shopify_id']

        db.commit()
        db.refresh(user)
        return user.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
