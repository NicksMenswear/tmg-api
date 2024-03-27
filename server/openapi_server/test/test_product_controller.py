# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from models.product_item import ProductItem  # noqa: E501
from test import BaseTestCase


class TestProductController(BaseTestCase):
    """ProductController integration test stubs"""

    def test_create_product_item(self):
        """Test case for create_product_item

        Create product item
        """
        product_item = {
  "price" : 6.0274563,
  "name" : "name",
  "description" : "description",
  "id" : 0
}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/v1/product',
            method='POST',
            headers=headers,
            data=json.dumps(product_item),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_product_items(self):
        """Test case for list_product_items

        Lists all product items
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/product',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
