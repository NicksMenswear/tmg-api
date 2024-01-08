# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from openapi_server.models.audit_log import AuditLog  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAuditController(BaseTestCase):
    """AuditController integration test stubs"""

    def test_list_audit_entries(self):
        """Test case for list_audit_entries

        Lists all audit entries
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v1/audit',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
