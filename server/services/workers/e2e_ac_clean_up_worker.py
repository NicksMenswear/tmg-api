import logging

from server.services.integrations.activecampaign_service import AbstractActiveCampaignService

logger = logging.getLogger(__name__)

EMAIL_SUFFIX_TO_MATCH = "@mail.dev.tmgcorp.net"
NUMBER_OF_CONTACTS_TO_PROCESS = 100

SYSTEM_E2E_EMAILS_TO_KEEP = {
    "e2e+01@mail.dev.tmgcorp.net",
    "e2e+02@mail.dev.tmgcorp.net",
    "e2e+03@mail.dev.tmgcorp.net",
    "e2e+04@mail.dev.tmgcorp.net",
    "e2e+05@mail.dev.tmgcorp.net",
}


class E2EActiveCampaignCleanUpWorker:
    def __init__(self, active_campaign_service: AbstractActiveCampaignService):
        self.active_campaign_service = active_campaign_service

    def cleanup(self) -> None:
        contacts = self.active_campaign_service.get_contacts_by_email_suffix(
            EMAIL_SUFFIX_TO_MATCH, NUMBER_OF_CONTACTS_TO_PROCESS
        )

        if not contacts:
            logger.debug("No test contacts found to clean up ...")
            return

        for contact in contacts:
            contact_id = contact.get("id")
            email = contact.get("email")

            if email in SYSTEM_E2E_EMAILS_TO_KEEP:
                logger.info(f"Skipping system contact: {email}")
                continue

            logger.info(f"Removing contact {contact_id} with email {contact.get('email')} ...")

            try:
                self.active_campaign_service.delete_contact(contact_id)
            except Exception:
                logger.exception(f"Failed to delete contact {contact_id} with email {contact.get('email')}")
