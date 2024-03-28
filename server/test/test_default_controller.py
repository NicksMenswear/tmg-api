# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_events_username_get(self):
        """Test case for events_username_get

        
        """
        headers = { 
        }
        response = self.client.open(
            '/v1/events/{username}'.format(username='username_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
