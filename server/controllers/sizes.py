import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.size_model import CreateSizeRequestModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create(data):
    sizing_service = FlaskApp.current().size_service
    order_service = FlaskApp.current().order_service

    sizing_model = sizing_service.create_size(CreateSizeRequestModel(**data))
    order_service.update_user_pending_orders_with_latest_measurements(sizing_model)

    return {"id": sizing_model.id}, 201
