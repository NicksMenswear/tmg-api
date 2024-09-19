import json

from server.tests.integration import BaseTestCase, fixtures


class TestSuitBuilder(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants()

    def test_add_item(self):
        # given
        item = fixtures.add_suit_builder_item_request()

        # when
        response = self.client.open(
            "/admin/suit-builder/items",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(item.model_dump()),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json.get("id"))
        self.assertEqual(response.json.get("type"), item.type)
        self.assertEqual(response.json.get("sku"), item.sku)

    def test_add_item_duplicate_sku(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)

        # when
        response = self.client.open(
            "/admin/suit-builder/items",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(item.model_dump()),
        )

        # then
        self.assertStatus(response, 409)

    def test_get_items(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(fixtures.add_suit_builder_item_request())

        # when
        response = self.client.open(
            "/admin/suit-builder/items",
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json.get(item.type)), 1)
        self.assertEqual(response.json.get(item.type)[0].get("sku"), item.sku)
        self.assertIsNone(response.json.get(item.type)[0].get("id"))
        self.assertIsNone(response.json.get(item.type)[0].get("product_id"))
        self.assertIsNone(response.json.get(item.type)[0].get("is_active"))

    def test_get_items_enriched(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(fixtures.add_suit_builder_item_request())

        # when
        response = self.client.open(
            "/admin/suit-builder/items",
            method="GET",
            query_string={"enriched": True},
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json.get(item.type)), 1)
        self.assertEqual(response.json.get(item.type)[0].get("sku"), item.sku)
        self.assertIsNotNone(response.json.get(item.type)[0].get("id"))
        self.assertIsNotNone(response.json.get(item.type)[0].get("product_id"))
        self.assertIsNotNone(response.json.get(item.type)[0].get("is_active"))
