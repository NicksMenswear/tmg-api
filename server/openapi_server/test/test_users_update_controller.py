# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestUsersUpdateController(BaseTestCase):
    """UsersUpdateController integration test stubs"""

    def test_update_user(self):
        """Test case for update_user

        Update a user by ID
        """
        user = {
  "size" : "size",
  "id" : 0,
  "email" : "email",
  "username" : "username"
}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/v1/users/{user_id}'.format(user_id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(user),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
