import unittest

from flask import json

from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestUsersCreateController(BaseTestCase):
    """UsersCreateController integration test stubs"""

    def test_create_user(self):
        """Test case for create_user

        Create user
        """
        user = {"size":"size","id":0,"email":"email","username":"username"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/v1/users',
            method='POST',
            headers=headers,
            data=json.dumps(user),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
