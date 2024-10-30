import base64
import json
import random
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
        self.assertIsNotNone(response_item.get("is_active"))
        self.assertIsNotNone(response_item.get("image_url"))
        self.assertIsNotNone(response_item.get("icon_url"))

    def test_patch_item_is_active(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)

        # when
        response = self.client.open(
            f"/admin/suit-builder/items/{item.sku}",
            method="PATCH",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps({"field": "is_active", "value": False}),
        )

        # then
        self.assertStatus(response, 200)
        self.assertFalse(response.json.get("is_active"))

    def test_patch_item_index(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)
        new_index = random.randint(1, 100)

        # when
        response = self.client.open(
            f"/admin/suit-builder/items/{item.sku}",
            method="PATCH",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps({"field": "index", "value": new_index}),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json.get("index"), new_index)

    def test_patch_item_image(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)

        # when
        image_b64 = self.__file_to_b64("assets/look_1.png")

        response = self.client.open(
            f"/admin/suit-builder/items/{item.sku}",
            method="PATCH",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps({"field": "image_b64", "value": image_b64}),
        )

        # then
        self.assertStatus(response, 200)
        self.assertIsNotNone(response.json.get("image_url"))

    def test_patch_item_icon(self):
        # given
        item = fixtures.add_suit_builder_item_request()
        self.suit_builder_service.add_item(item)

        # when
        icon_b64 = self.__file_to_b64("assets/look_1.png")

        response = self.client.open(
            f"/admin/suit-builder/items/{item.sku}",
            method="PATCH",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps({"field": "icon_b64", "value": icon_b64}),
        )

        # then
        self.assertStatus(response, 200)
        self.assertIsNotNone(response.json.get("image_url"))

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

    @staticmethod
    def __file_to_b64(file_path):
        with open(file_path, "rb") as file:
            content = file.read()

        return base64.b64encode(content).decode("utf-8")
