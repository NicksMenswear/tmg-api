from openapi_server.database.database_manager import get_database_session  # noqa: E501
from openapi_server.database.models import User
from werkzeug.exceptions import HTTPException
from .shopify import get_activation_url, create_customer
from .activecampaign import create_contact
import uuid

db = get_database_session()

def send_invite(invite_data):  # noqa: E501
    """Send Invite

     # noqa: E501

    Customer-id
    First Name
    Last Name
    Customer email
    Event-id
    Event Name

    :rtype: None
    """
    try:
        existing_user = db.query(User).filter_by(email=invite_data['email']).first()
        if existing_user:
            if existing_user.account_status==False:
                activation_url = ""
            else:
                activation_url = get_activation_url(existing_user.shopify_id)
                print('act url: ',activation_url)

            data = {
                'email': invite_data['email'],
                'first_name': invite_data['first_name'],
                'last_name': invite_data['last_name'],
                'event_name': invite_data['event_name'],
                'event_id': invite_data['event_id'],
                'activation_url': activation_url
            }
            create_contact(data)
            return "Invitation sent successfully"       
        else:
            shopify_id = create_customer({
                'first_name' : invite_data['first_name'],
                'last_name' : invite_data['last_name'],
                'email' : invite_data['email'],
            })

            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                first_name=invite_data['first_name'],
                last_name=invite_data['last_name'],
                email=invite_data['email'],
                shopify_id=shopify_id,
                account_status = True,
                role = None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            activation_url = get_activation_url(shopify_id)
            print('act url: ',activation_url)

            data = {
                'email': invite_data['email'],
                'first_name': invite_data['first_name'],
                'last_name': invite_data['last_name'],
                'event_name': invite_data['event_name'],
                'event_id': invite_data['event_id'],
                'activation_url': activation_url
            }
            create_contact(data)
            return "Invitation sent successfully"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    finally:
        db.close()
