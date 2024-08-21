import logging

from sqlalchemy import func

from server.database.job_db_manager import get_db_session
from server.database.models import User
from server.models.user_model import UserModel

logger = logging.getLogger(__name__)


def add_expedited_shipping_for_suit_bundles():
    try:
        logger.info(f"add_expedited_shipping_for_suit_bundles...")

        email = "zinovii+01@themoderngroom.com"

        with next(get_db_session()) as session:
            user = session.query(User).filter(func.lower(User.email) == email.lower()).first()

            if user:
                print(user.first_name)
                print(UserModel.from_orm(user))
    except Exception as e:
        logger.error(f"Error adding expedited shipping for suit bundles: {e}")
        raise e
