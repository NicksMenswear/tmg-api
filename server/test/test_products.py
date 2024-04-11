from __future__ import absolute_import

import json
import unittest
import uuid

from server import encoder
from server.database.models import ProductItem
from server.test import BaseTestCase, CONTENT_TYPE_JSON

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


class TestProducts(BaseTestCase):
    def setUp(self):
        super(TestProducts, self).setUp()

        self.db = self.session()
        self.db.query(ProductItem).delete()
        self.db.commit()
        self.request_headers = {
            "Accept": CONTENT_TYPE_JSON,
        }

    @staticmethod
    def create_product_request_payload(**kwargs):
        return {
            "name": kwargs.get("name", str(uuid.uuid4())),
            "Active": kwargs.get("is_active", True),
            "SKU": kwargs.get("sku", str(uuid.uuid4())),
            "Weight": kwargs.get("weight", 1.0),
            "Height": kwargs.get("height", 1.0),
            "Width": kwargs.get("width", 1.0),
            "Length": kwargs.get("length", 1.0),
            "Value": kwargs.get("value", 1.0),
            "Price": kwargs.get("price", 1.0),
            "On_hand": kwargs.get("on_hand", 1),
            "Allocated": kwargs.get("allocated", 1),
            "Reserve": kwargs.get("reserve", 1),
            "Non_sellable_total": kwargs.get("non_sellable_total", 1),
            "Reorder_level": kwargs.get("reorder_level", 1),
            "Reorder_amount": kwargs.get("reorder_amount", 1),
            "Replenishment_level": kwargs.get("replenishment_level", 1),
            "Available": kwargs.get("available", 1),
            "Backorder": kwargs.get("backorder", 1),
            "Barcode": kwargs.get("barcode", 123456),
            "Tags": kwargs.get("tags", ["tag1", "tag2"]),
        }

    @staticmethod
    def create_db_product(**kwargs):
        return ProductItem(
            id=kwargs.get("id", str(uuid.uuid4())),
            is_active=kwargs.get("is_active", True),
            name=kwargs.get("name", str(uuid.uuid4())),
            sku=kwargs.get("SKU", str(uuid.uuid4())),
            weight_lb=kwargs.get("Weight", 1.0),
            height_in=kwargs.get("Height", 1.0),
            width_in=kwargs.get("Width", 1.0),
            length_in=kwargs.get("Length", 1.0),
            value=kwargs.get("Value", 1.0),
            price=kwargs.get("Price", 1.0),
            on_hand=kwargs.get("On_hand", 1),
            allocated=kwargs.get("Allocated", 1),
            reserve=kwargs.get("Reserve", 1),
            non_sellable_total=kwargs.get("Non_sellable_total", 1),
            reorder_level=kwargs.get("Reorder_level", 1),
            reorder_amount=kwargs.get("Reorder_amount", 1),
            replenishment_level=kwargs.get("Replenishment_level", 1),
            available=kwargs.get("Available", 1),
            backorder=kwargs.get("Backorder", 1),
            barcode=kwargs.get("Barcode", 1234567890),
            tags=kwargs.get("Tags", ["tag1", "tag2"]),
        )

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
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert404(response)

    def test_get_existing_product_by_id(self):
        # given
        product_id = str(uuid.uuid4())
        product = self.create_db_product(id=product_id)
        self.db.add(product)
        self.db.commit()

        # when
        query_params = {**self.hmac_query_params, "product_id": product_id}
        response = self.client.open("/product".format(id=product_id), query_string=query_params, method="GET")

        # then
        self.assert200(response)
        self.assert_equal_response_product_with_db_product(product, response.json)

    def test_get_existing_product_by_id_but_not_active(self):
        # given
        product_id = str(uuid.uuid4())
        product = self.create_db_product(id=product_id, is_active=False)
        self.db.add(product)
        self.db.commit()

        # when
        query_params = {**self.hmac_query_params, "product_id": product_id}
        response = self.client.open("/product".format(id=product_id), query_string=query_params, method="GET")

        # then
        self.assert404(response)

    def test_create_product(self):
        # given
        product = self.create_product_request_payload()

        # when
        response = self.client.open(
            "/products",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
            data=json.dumps(product, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_left(product, response.json)
        self.assertIsNotNone(response.json["id"])

    def test_create_product_with_existing_name(self):
        # given
        product_name = str(uuid.uuid4())
        product = self.create_db_product(name=product_name)
        product_request = self.create_product_request_payload(name=product_name)
        self.db.add(product)
        self.db.commit()

        # when
        response = self.client.open(
            "/products",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
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
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_products(self):
        # given
        product1 = self.create_db_product()
        product2 = self.create_db_product()
        self.db.add(product1)
        self.db.add(product2)
        self.db.commit()

        # when
        response = self.client.open(
            "/products",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_equal_response_product_with_db_product(product1, response.json[0])
        self.assert_equal_response_product_with_db_product(product2, response.json[1])

    def test_get_list_of_products_excluding_non_active(self):
        # given
        product1 = self.create_db_product()
        product2 = self.create_db_product(is_active=False)
        self.db.add(product1)
        self.db.add(product2)
        self.db.commit()

        # when
        response = self.client.open(
            "/products",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 1)
        self.assert_equal_response_product_with_db_product(product1, response.json[0])

    def test_update_non_existing_product(self):
        # given
        product = self.create_product_request_payload()
        product["id"] = str(uuid.uuid4())

        # when
        response = self.client.open(
            "/update_product",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(product, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert404(response)

    def test_update_product(self):
        # given
        product = self.create_db_product()
        self.db.add(product)
        self.db.commit()

        # when
        updated_product = self.create_product_request_payload(
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
            content_type=CONTENT_TYPE_JSON,
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
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert404(response)

    # def test_delete_non_existing_product(self):
    #     # given
    #     delete_product_payload = {"id": str(uuid.uuid4()), "is_active": False}
    #
    #     # when
    #     response = self.client.open(
    #         "/delete_product",
    #         query_string=self.hmac_query_params,
    #         method="PUT",
    #         data=json.dumps(delete_product_payload, cls=encoder.CustomJSONEncoder),
    #         headers=self.request_headers,
    #         content_type=CONTENT_TYPE_JSON,
    #     )
    #
    #     # then
    #     self.assert404(response)
