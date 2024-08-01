import logging
import uuid

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.size_model import CreateSizeRequestModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create(data):
    sizing_service = FlaskApp.current().size_service
    order_service = FlaskApp.current().order_service

    size = sizing_service.create_size(CreateSizeRequestModel(**data))
    order_service.update_user_pending_orders_with_latest_measurements(size)

    return size.to_response(), 201


@hmac_verification
@error_handler
def get_latest_size(user_id):
    sizing_service = FlaskApp.current().size_service

    size = sizing_service.get_latest_size_for_user(uuid.UUID(user_id))

    return size.to_response() if size else None, 201
