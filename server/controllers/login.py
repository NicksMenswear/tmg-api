import os
import json
import logging

from server.database.models import User
from server.database.database_manager import db
from server.controllers.util import hmac_verification, http

logger = logging.getLogger(__name__)


shopify_store = os.getenv("shopify_store")
admin_api_access_token = os.getenv("admin_api_access_token")


@hmac_verification
def login_val(email):
    try:

        user = db.session.query(User).filter(User.email == email).first()
        response = http(
            "GET",
            f"https://{shopify_store}.myshopify.com/admin/api/2024-01/customers/search.json?query=email:{email}",
            headers={
                "X-Shopify-Access-Token": admin_api_access_token,
            },
        )
        customers_response = json.loads(response.data.decode("utf-8")).get("customers", [])
        if isinstance(customers_response, list):
            if len(customers_response) > 0:
                state = customers_response[0]["state"]
                if user is not None:
                    return {"tmg_state": user.account_status, "shopify_state": state}, 200
                else:
                    return {"tmg_state": "User not found", "shopify_state": state}, 200
            elif len(customers_response) == 0:
                if user is not None:
                    return {"tmg_state": user.account_status, "shopify_state": "User not found"}, 200
                else:
                    return {"tmg_state": "User not found", "shopify_state": "User not found"}, 404
    except Exception as e:
        logger.info(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
