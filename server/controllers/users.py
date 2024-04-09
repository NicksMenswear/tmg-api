from server.database.models import User
from server.database.database_manager import get_database_session
from server.controllers.shopify import create_customer, get_activation_url
from server.controllers.registration_email import send_email
import uuid
from server.controllers.hmac_1 import hmac_verification
import os
from urllib.parse import unquote


password = os.getenv("sender_password")
sender_email = os.getenv("sender_email")


db = get_database_session()


@hmac_verification()
def create_user(user_data):  # noqa: E501
    """Create user

    :param user_data:
    :type user_data: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """  # noqa: E501
    try:
        existing_user = db.query(User).filter_by(email=user_data["email"]).first()
        if existing_user:
            return "User with the same email already exists in TMG Database!", 400

        try:
            shopify_id = create_customer(
                {
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "email": user_data["email"],
                }
            )
            print("shopify_id 111111111 ===============: ", shopify_id)
        except Exception as e:
            print(e)
            return "User not created in shopify", 400

        print("shopify_id ===============: ", shopify_id)
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            shopify_id=shopify_id,
            account_status=user_data["account_status"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        activation_url = get_activation_url(shopify_id)
        activation_link = f'<a href="{activation_url}">Click Me</a>'
        body = f"Click the following link to activate your account: {activation_link}"

        sender_password = password
        reciever = user_data["email"]
        subject = "Registration email"
        send_email(subject, body, sender_email, reciever, sender_password)

        return "User created successfully!", 201
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def get_user_by_id(email):  # noqa: E501
    """Get a single user by ID

     # noqa: E501

    :param user_id: Unique ID of the user to retrieve
    :type user_id: int

    :rtype: User
    """
    try:
        email = unquote(email)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"message": f"User with email '{email}' does not exist"}, 204
        formatted_user = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "shopify_id": user.shopify_id,
            "account_status": user.account_status,
        }
        return formatted_user
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


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
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "shopify_id": user.shopify_id,
                "account_status": user.account_status,
            }
            formatted_users.append(formatted_user)
        return formatted_users
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


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
        user = db.query(User).filter(User.email == user_data["email"]).first()

        if not user:
            return {"message": "User not found"}, 204

        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]
        user.shopify_id = user_data["shopify_id"]
        user.account_status = user_data["account_status"]

        db.commit()
        db.refresh(user)
        return user.to_dict()
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
