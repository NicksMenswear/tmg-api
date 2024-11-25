import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.handlers import init_sentry
from server.services.integrations.activecampaign_service import ActiveCampaignService

init_sentry()

logger = Logger(service="e2e-active-campaign-clean-up")

EMAIL_SUFFIX_TO_MATCH = "@mail.dev.tmgcorp.net"
NUMBER_OF_CONTACTS_TO_PROCESS = 50

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
    active_campaign_service = ActiveCampaignService()

    contacts = active_campaign_service.get_contacts_by_email_suffix(
        EMAIL_SUFFIX_TO_MATCH, NUMBER_OF_CONTACTS_TO_PROCESS
    )

    if not contacts:
        logger.debug("No test contacts found to clean up ...")
        return

    for contact in contacts:
        email = contact.get("email")

        if email in SYSTEM_E2E_EMAILS_TO_KEEP:
            logger.info(f"Skipping system contact: {email}")
            continue

        contact_id = contact.get("id")

        logger.info(f"Removing contact {contact_id} with email {contact.get('email')} ...")

        try:
            active_campaign_service.delete_contact(contact_id)
        except Exception:
            logger.exception(f"Failed to delete contact {contact_id} with email {contact.get('email')}")

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}


def __in_test_context(context) -> bool:
    return isinstance(context, FakeLambdaContext)
