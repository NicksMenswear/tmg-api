from __future__ import absolute_import

import json
import unittest
import uuid

from server import encoder
from server.database.models import ProductItem
from server.services.legacy.product import ProductService
from server.test import BaseTestCase, fixtures

# TODO: Remove this key mapping once the API is fixed
PRODUCT_KEYS_MAPPING = {
    "id": "id",
    "name": "name",
    "Active": "is_active",
    "SKU": "sku",
    "Weight": "weight_lb",
    "Height": "height_in",
    "Width": "width_in",
    "Length": "length_in",
    "Value": "value",
    "Price": "price",
    "On_hand": "on_hand",
    "Allocated": "allocated",
    "Reserve": "reserve",
    "Non_sellable_total": "non_sellable_total",
    "Reorder_level": "reorder_level",
    "Reorder_amount": "reorder_amount",
    "Replenishment_level": "replenishment_level",
    "Available": "available",
    "Backorder": "backorder",
    "Barcode": "barcode",
    "Tags": "tags",
}


@unittest.skip("Products are not used at the moment.")
class TestProducts(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.product_service = ProductService()

    def assert_equal_response_product_with_db_product(self, product: ProductItem, response_product: dict):
        self.assertEqual(response_product.get("id"), str(product.id))
        self.assertEqual(response_product.get("is_active"), product.is_active)
        self.assertEqual(response_product.get("name"), product.name)
        self.assertEqual(response_product.get("sku"), product.sku)
        self.assertEqual(response_product.get("weight_lb"), product.weight_lb)
        self.assertEqual(response_product.get("height_in"), product.height_in)
        self.assertEqual(response_product.get("width_in"), product.width_in)
        self.assertEqual(response_product.get("length_in"), product.length_in)
        self.assertEqual(response_product.get("value"), product.value)
        self.assertEqual(response_product.get("price"), product.price)
        self.assertEqual(response_product.get("on_hand"), product.on_hand)
        self.assertEqual(response_product.get("allocated"), product.allocated)
        self.assertEqual(response_product.get("reserve"), product.reserve)
        self.assertEqual(response_product.get("non_sellable_total"), product.non_sellable_total)
        self.assertEqual(response_product.get("reorder_level"), product.reorder_level)
        self.assertEqual(response_product.get("reorder_amount"), product.reorder_amount)
        self.assertEqual(response_product.get("replenishment_level"), product.replenishment_level)
        self.assertEqual(response_product.get("available"), product.available)
        self.assertEqual(response_product.get("backorder"), product.backorder)
        self.assertEqual(response_product.get("barcode"), product.barcode)
        self.assertEqual(response_product.get("tags"), product.tags)

    def assert_equal_left(self, left, right):
        # Asserts that all key-value pairs in left are present and equal in right.
        # TODO: remove this and use from parent class once the API object fields are normalized
        for key in left:
            self.assertEqual(left[key], right[PRODUCT_KEYS_MAPPING[key]])

    def test_get_non_existing_product_by_id(self):
        # given
        query_params = {**self.hmac_query_params, "product_id": str(uuid.uuid4())}

        # when
        response = self.client.open(
            "/product",
            query_string=query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_existing_product_by_id(self):
        # given
        product = self.product_service.create_product(fixtures.product_request())

        # when
        query_params = {**self.hmac_query_params, "product_id": product.id}
        response = self.client.open("/product".format(id=product.id), query_string=query_params, method="GET")

        # then
        self.assert200(response)
        self.assert_equal_response_product_with_db_product(product, response.json)

    def test_get_existing_product_by_id_but_not_active(self):
        # given
        product_id = str(uuid.uuid4())
        self.product_service.create_product(fixtures.product_request(id=product_id, is_active=False))

        # when
        query_params = {**self.hmac_query_params, "product_id": product_id}
        response = self.client.open("/product".format(id=product_id), query_string=query_params, method="GET")

        # then
        self.assert404(response)

    def test_create_product(self):
        # given
        product = fixtures.product_request()

        # when
        response = self.client.open(
            "/products",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(product, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_left(product, response.json)
        self.assertIsNotNone(response.json["id"])

    def test_create_product_with_existing_name(self):
        # given
        product_name = f"product-{str(uuid.uuid4())}"
        product = self.product_service.create_product(fixtures.product_request(name=product_name))

        # when
        product_request = fixtures.product_request(name=product_name)
        response = self.client.open(
            "/products",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(product_request, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 409)

    def test_get_list_of_products_from_empty_db(self):
        # when
        response = self.client.open(
            "/products",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_products(self):
        # given
        product1 = self.product_service.create_product(fixtures.product_request())
        product2 = self.product_service.create_product(fixtures.product_request())

        # when
        response = self.client.open(
            "/products",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_equal_response_product_with_db_product(product1, response.json[0])
        self.assert_equal_response_product_with_db_product(product2, response.json[1])

    def test_get_list_of_products_excluding_non_active(self):
        # given
        product1 = self.product_service.create_product(fixtures.product_request())
        self.product_service.create_product(fixtures.product_request(is_active=False))

        # when
        response = self.client.open(
            "/products",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 1)
        self.assert_equal_response_product_with_db_product(product1, response.json[0])

    def test_update_non_existing_product(self):
        # given
        product = fixtures.product_request()
        product["id"] = str(uuid.uuid4())

        # when
        response = self.client.open(
            "/update_product",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(product, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_update_product(self):
        # given
        product = self.product_service.create_product(fixtures.product_request())

        # when
        updated_product = fixtures.product_request(
            id=str(product.id),
            name=product.name + "-updated",
            price=product.price + 1,
            weight=product.weight_lb + 1,
            height=product.height_in + 1,
            width=product.width_in + 1,
            length=product.length_in + 1,
            value=product.value + 1,
            on_hand=product.on_hand + 1,
            allocated=product.allocated + 1,
            reserve=product.reserve + 1,
            non_sellable_total=product.non_sellable_total + 1,
            reorder_level=product.reorder_level + 1,
            reorder_amount=product.reorder_amount + 1,
            replenishment_level=product.replenishment_level + 1,
            available=product.available + 1,
            backorder=product.backorder + 1,
            barcode=product.barcode + 1,
            tags=product.tags + ["tag3"],
        )

        updated_product["id"] = str(product.id)

        response = self.client.open(
            "/update_product",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_product, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assert_equal_left(updated_product, response.json)

    @unittest.skip("this should fail on validation phase")
    def test_update_product_missing_required_fields(self):
        pass

    def test_delete_non_existing_product(self):
        # given
        delete_product_payload = {"id": str(uuid.uuid4()), "is_active": False}

        # when
        response = self.client.open(
            "/delete_product",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(delete_product_payload, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_delete_product(self):
        # given
        product = self.product_service.create_product(fixtures.product_request())
        delete_product_payload = {"id": product.id, "is_active": False}

        # when
        response = self.client.open(
            "/delete_product",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(delete_product_payload, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)
