import json
import os
import random

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.handlers import init_sentry
from server.services.integrations.shopify_service import ShopifyService
from server.services.workers.e2e_clean_up_worker import E2ECleanUpWorker

init_sentry()

logger = Logger(service="e2e-clean-up")

CUSTOMER_EMAIL_MATCHING_PATTERN = "e2e+*@mail.dev.tmgcorp.net"
ONLINE_STORE_SALES_CHANNEL_ID = os.getenv("online_store_sales_channel_id", "gid://shopify/Publication/94480072835")
SYSTEM_E2E_EMAILS_TO_KEEP = {
    "e2e+01@mail.dev.tmgcorp.net",
    "e2e+02@mail.dev.tmgcorp.net",
    "e2e+03@mail.dev.tmgcorp.net",
    "e2e+04@mail.dev.tmgcorp.net",
    "e2e+05@mail.dev.tmgcorp.net",
    "e2e+06@mail.dev.tmgcorp.net",
    "e2e+07@mail.dev.tmgcorp.net",
    "e2e+08@mail.dev.tmgcorp.net",
    "e2e+09@mail.dev.tmgcorp.net",
    "e2e+10@mail.dev.tmgcorp.net",
}


class FakeLambdaContext(LambdaContext):
    def __init__(self):
        self._function_name = "test_function"
        self._memory_limit_in_mb = 128
        self._invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
        self._aws_request_id = "test-request-id"


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    e2e_clean_up_worker = E2ECleanUpWorker(ShopifyService(ONLINE_STORE_SALES_CHANNEL_ID), logger)
    customers = e2e_clean_up_worker.get_customers(20)

    non_system_customers = [
        customer for customer in customers if customer.get("email") not in SYSTEM_E2E_EMAILS_TO_KEEP
    ]

    for customer in non_system_customers:
        logger.info(f"Processing customer: {customer.get('email')}")

        e2e_clean_up_worker.cleanup(customer.get("id"), customer.get("email"))

    system_customers = [customer for customer in customers if customer.get("email") in SYSTEM_E2E_EMAILS_TO_KEEP]
    random.shuffle(system_customers)

    # processing only 3 at a time of system e2e customers
    for customer in system_customers[: min(3, len(system_customers))]:
        logger.info(f"Processing system customer: {customer.get('email')}")

        e2e_clean_up_worker.cleanup(customer.get("id"), customer.get("email"))

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}


def __in_test_context(context) -> bool:
    return isinstance(context, FakeLambdaContext)


if __name__ == "__main__":
    lambda_handler({}, FakeLambdaContext())
