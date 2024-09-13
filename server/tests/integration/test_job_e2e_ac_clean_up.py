import random

from server.tests import utils
from server.tests.integration import BaseTestCase


class TestJobE2EActiveCampaignCleanUp(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_e2e_ac_clean_no_contacts(self):
        # when
        response = self.client.open(
            "/jobs/system/e2e-ac-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertStatus(response, 200)

    def test_e2e_ac_clean_only_test_contacts(self):
        # given
        email1 = utils.generate_email()
        email2 = utils.generate_email()
        email3 = f"{random.randint(10000, 1000000)}@example.com"

        self.activecampaign_service.contacts.append({"id": random.randint(10000, 100000), "email": email1})
        self.activecampaign_service.contacts.append({"id": random.randint(10000, 100000), "email": email2})
        self.activecampaign_service.contacts.append({"id": random.randint(10000, 100000), "email": email3})

        # when
        self.assertTrue(len(self.activecampaign_service.contacts) == 3)

        response = self.client.open(
            "/jobs/system/e2e-ac-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertTrue(len(self.activecampaign_service.contacts) == 1)
        self.assertTrue(self.activecampaign_service.contacts[0]["email"] == email3)

        self.assertStatus(response, 200)

    def test_e2e_ac_clean_keep_system_contacts(self):
        # given
        email1 = utils.generate_email()
        email2 = f"e2e+01@mail.dev.tmgcorp.net"

        self.activecampaign_service.contacts.append({"id": random.randint(10000, 100000), "email": email1})
        self.activecampaign_service.contacts.append({"id": random.randint(10000, 100000), "email": email2})

        # when
        self.assertTrue(len(self.activecampaign_service.contacts) == 2)

        response = self.client.open(
            "/jobs/system/e2e-ac-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertTrue(len(self.activecampaign_service.contacts) == 1)
        self.assertTrue(self.activecampaign_service.contacts[0]["email"] == email2)

        self.assertStatus(response, 200)
