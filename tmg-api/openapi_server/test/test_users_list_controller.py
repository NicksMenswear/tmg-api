import unittest

from flask import json

from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestUsersListController(BaseTestCase):
    """UsersListController integration test stubs"""

    def test_list_users(self):
        """Test case for list_users

        Lists all users
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/users',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
