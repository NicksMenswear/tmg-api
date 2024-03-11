import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from openapi_server.database.models import User, Event, Order, OrderItem
from openapi_server.database.database_manager import get_database_session
from .shopify import create_customer, get_customer ,get_activation_url
from .registration_email import send_email
import uuid
from werkzeug.exceptions import HTTPException
from .hmac_1 import hmac_verification


db = get_database_session()


@hmac_verification()
def create_user(user_data):  # noqa: E501
    """Create user

    :param user_data:
    :type user_data: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """ # noqa: E501
    try:
        existing_user = db.query(User).filter_by(email=user_data['email']).first()
        shopify_user = get_customer(user_data['email'])
        if (existing_user and shopify_user):
            return 'user with the same email already exists!', 400
        
        shopify_id = create_customer({
            'first_name' : user_data['first_name'],
            'last_name' : user_data['last_name'],
            'email' : user_data['email'],
        })

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            shopify_id=shopify_id,
            account_status = user_data['account_status'],
            role = user_data['role']
        )

        # activation_url = get_activation_url(shopify_id)               
        # sender_email='ali@themoderngroom.com'
        # sender_password='Sailors321!@#$'
        # reciever = user_data['email']
        # subject ='registration email'
        # send_mail = send_email(subject , activation_url ,sender_email,reciever,sender_password)
        # print('send email------------------' , send_mail)
        # return 'user creater'
        # send_mail = send_email(shopify_id , activation_url ,user_data['email'])
        # return 'user created'

        db.add(user)
        db.commit()
        db.refresh(user)
    
        
        return 'User created successfully!', 201
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@hmac_verification()
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
            return {"message":f"User with email '{email}' does not exist"}, 204
        formatted_user = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'shopify_id': user.shopify_id,
            'account_status' : user.account_status,
            'role' : user.role
        }
        return formatted_user
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@hmac_verification()
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
                'account_status' : user.account_status,
                'role' : user.role
            }
            formatted_users.append(formatted_user)
        return formatted_users
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@hmac_verification()
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
            return {"message":"User not found"}, 204
        
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.shopify_id = user_data['shopify_id']
        user.account_status = user_data['account_status']
        user.role = user_data['role']

        db.commit()
        db.refresh(user)
        return user.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
