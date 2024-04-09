# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from models.order import Order  # noqa: E501
from test import BaseTestCase


class TestOrdersGetController(BaseTestCase):
    """OrdersGetController integration test stubs"""

    def test_get_order_by_id(self):
        """Test case for get_order_by_id

        Retrieve a specific order by ID
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open("/v1/orders/{order_id}".format(order_id=56), method="GET", headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
