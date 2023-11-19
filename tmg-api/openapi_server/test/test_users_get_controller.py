import unittest

from flask import json

from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestUsersGetController(BaseTestCase):
    """UsersGetController integration test stubs"""

    def test_get_user_by_id(self):
        """Test case for get_user_by_id

        Get a single user by ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/users/{user_id}'.format(user_id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
