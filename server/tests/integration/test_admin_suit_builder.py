import json
import uuid

from server.database.models import SuitBuilderItem
from server.tests.integration import BaseTestCase, fixtures


class TestAdminSuitBuilder(BaseTestCase):
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
        self.suit_builder_service.add_item(item)

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
        response_item = response.json.get(item.type)[0]
        self.assertEqual(response_item.get("sku"), item.sku)
        self.assertIsNone(response_item.get("id"))
        self.assertIsNone(response_item.get("product_id"))
        self.assertIsNone(response_item.get("is_active"))
        self.assertIsNotNone(response_item.get("image_url"))
        self.assertIsNotNone(response_item.get("icon_url"))

    def test_get_items_enriched(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)

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
        response_item = response.json.get(item.type)[0]
        self.assertEqual(response_item.get("sku"), item.sku)
        self.assertIsNotNone(response_item.get("id"))
        self.assertIsNotNone(response_item.get("product_id"))
        self.assertIsNotNone(response_item.get("is_active"))
        self.assertIsNotNone(response_item.get("image_url"))
        self.assertIsNotNone(response_item.get("icon_url"))

    def test_delete_item(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)

        # when
        response = self.client.open(
            f"/admin/suit-builder/items/{item.sku}",
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)

        db_item = SuitBuilderItem.query.filter(SuitBuilderItem.sku == item.sku).first()
        self.assertIsNone(db_item)

    def test_delete_item_non_existed(self):
        # when
        response = self.client.open(
            f"/admin/suit-builder/items/{str(uuid.uuid4())}",
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)
