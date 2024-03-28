# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from models.event import Event  # noqa: E501
from test import BaseTestCase


class TestEventsController(BaseTestCase):
    """EventsController integration test stubs"""

    def test_openapi_server_contollers_events_contoller_create_event(self):
        """Test case for openapi_server_contollers_events_contoller_create_event

        Create event
        """
        event = {
  "date" : "2000-01-23T04:56:07.000+00:00",
  "id" : 0,
  "type" : "type"
}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/v1/events',
            method='POST',
            headers=headers,
            data=json.dumps(event),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
