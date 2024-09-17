import logging
from typing import Optional

from server.controllers.util import token_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@token_verification
@error_handler
def get_e2e_customers_to_clean_up():
    e2e_cleanup_worker = FlaskApp.current().e2e_cleanup_worker
    customers = e2e_cleanup_worker.get_customers()

    return customers, 200


@token_verification
@error_handler
def e2e_clean_up(customer=None):
    e2e_cleanup_worker = FlaskApp.current().e2e_cleanup_worker

    if customer:
        e2e_cleanup_worker.cleanup(customer.get("id"), customer.get("email"))
    else:
        e2e_cleanup_worker.bulk_cleanup()

    return {}, 200


@token_verification
@error_handler
def e2e_ac_clean_up():
    e2e_ac_cleanup_worker = FlaskApp.current().e2e_ac_cleanup_worker
    e2e_ac_cleanup_worker.cleanup()

    return {}, 200
