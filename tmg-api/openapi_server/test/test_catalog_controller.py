import unittest

from flask import json

from openapi_server.models.catalog_item import CatalogItem  # noqa: E501
from openapi_server.test import BaseTestCase


class TestCatalogController(BaseTestCase):
    """CatalogController integration test stubs"""

    def test_create_catalog_item(self):
        """Test case for create_catalog_item

        Create catalog item
        """
        catalog_item = {"price":6.0274563,"name":"name","description":"description","id":0}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/v1/catalog',
            method='POST',
            headers=headers,
            data=json.dumps(catalog_item),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_catalog_items(self):
        """Test case for list_catalog_items

        Lists all catalog items
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/catalog',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
