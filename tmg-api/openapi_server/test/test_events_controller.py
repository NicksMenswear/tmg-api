import unittest

from flask import json

from openapi_server.models.event import Event  # noqa: E501
from openapi_server.test import BaseTestCase


class TestEventsController(BaseTestCase):
    """EventsController integration test stubs"""

    def test_create_event(self):
        """Test case for create_event

        Create event
        """
        event = {"date":"2000-01-23T04:56:07.000+00:00","id":0,"type":"type"}
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

    def test_list_events(self):
        """Test case for list_events

        Lists all events
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/events',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
