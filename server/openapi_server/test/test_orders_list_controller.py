# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from openapi_server.models.order import Order  # noqa: E501
from openapi_server.test import BaseTestCase


class TestOrdersListController(BaseTestCase):
    """OrdersListController integration test stubs"""

    def test_get_orders(self):
        """Test case for get_orders

        Retrieve all orders, optionally filtered by user ID or event ID
        """
        query_string = [('user_id', 56),
                        ('event_id', 56)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/orders',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
