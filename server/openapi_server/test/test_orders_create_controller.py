# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from openapi_server.models.order import Order  # noqa: E501
from openapi_server.test import BaseTestCase


class TestOrdersCreateController(BaseTestCase):
    """OrdersCreateController integration test stubs"""

    def test_create_order(self):
        """Test case for create_order

        Create order
        """
        order = {
  "order_date" : "2000-01-23T04:56:07.000+00:00",
  "event_id" : 1,
  "user_id" : 6,
  "received_date" : "2000-01-23T04:56:07.000+00:00",
  "shipped_date" : "2000-01-23T04:56:07.000+00:00",
  "id" : 0,
  "items" : [ {
    "catalog_item_id" : 5,
    "quantity" : 5,
    "price" : 2.302136
  }, {
    "catalog_item_id" : 5,
    "quantity" : 5,
    "price" : 2.302136
  } ]
}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/v1/orders',
            method='POST',
            headers=headers,
            data=json.dumps(order),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
