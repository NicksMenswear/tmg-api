from server.controllers.util import token_verification, log_request
from server.flask_app import FlaskApp


@token_verification
@log_request
def add_expedited_shipping_for_suit_bundles():
    look_service = FlaskApp.current().look_service

    looks = look_service.add_expedited_shipping_for_suit_bundle()

    return looks, 200
