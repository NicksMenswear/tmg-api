import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from openapi_server.database.models import User, Event, Order, OrderItem
from openapi_server.database.database_manager import get_database_session
import uuid
from werkzeug.exceptions import HTTPException

db = get_database_session()

def create_user(user_data):  # noqa: E501
    """Create user

    :param user_data:
    :type user_data: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """ # noqa: E501
    try:
        existing_user = db.query(User).filter_by(email=user_data['email']).first()
        if existing_user:
            return 'user with the same email already exists!', 400
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            shopify_id=user_data['shopify_id'],
            temp = 'true',
            role = user_data['role']
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return 'User created successfully!', 201
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_user_by_id(email):  # noqa: E501
    """Get a single user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to retrieve
    :type user_id: int

    :rtype: User
    """
    try:
        user = db.query(User).filter(User.email==email).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with email '{email}' does not exist")
        formatted_user = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'shopify_id': user.shopify_id,
            'temp' : user.temp,
            'role' : user.role
        }
        return formatted_user
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
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
        user.temp = user_data['temp']
        user.role = user_data['role']

        db.commit()
        db.refresh(user)
        return user.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
# def delete_user(email):  # Logic for deletion of user is implemented but need change in schema to work correctly
#     """ Deleting user using email"""
#     try:
#         user = db.query(User).filter(User.email==email).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
#         order = db.query(Order).filter(Order.user_id==user.id).first()
#         if not order:
#             raise HTTPException(status_code=404, detail="Order not found")
#         order_items = db.query(OrderItem).filter(OrderItem.order_id==order.id)
#         for order_item in order_items:
#             db.delete(order_item)

#         db.commit()
#         db.delete(order)
#         db.commit()

#         user_events = db.query(Event).filter(Event.user_id==user.id)
#         for user_event in user_events:
#             db.delete(user_event)

#         db.commit()
#         db.delete(user)
#         db.commit()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Internal Server Error")
    