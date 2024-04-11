from __future__ import absolute_import

import unittest
import uuid

from server.database.models import ProductItem
from server.test import BaseTestCase


class TestProducts(BaseTestCase):
    def setUp(self):
        super(TestProducts, self).setUp()

        self.db = self.session()
        self.db.query(ProductItem).delete()
        self.db.commit()
        self.request_headers = {
            "Accept": "application/json",
        }

    @staticmethod
    def create_product_request_payload(**kwargs):
        return {
            "name": kwargs.get("name", str(uuid.uuid4())),
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
            "Barcode": kwargs.get("barcode", 1234567890),
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
        for key in left:
            self.assertEqual(left[key], right[key])

    def test_get_non_existing_product_by_id(self):
        # given
        query_params = {**self.hmac_query_params, "product_id": str(uuid.uuid4())}

        # when
        response = self.client.open(
            "/product",
            query_string=query_params,
            method="GET",
            content_type="application/json",
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

    def test_create_product(self):
        # given
        product = self.create_product_request_payload()

        # when
        response = self.client.open(
            "/products",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            data=product,
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_left(product, response.json)
        self.assertIsNotNone(response.json["id"])


if __name__ == "__main__":
    unittest.main()
