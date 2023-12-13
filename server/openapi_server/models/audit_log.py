# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
from openapi_server import util


class AuditLog(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None):  # noqa: E501
        """AuditLog - a model defined in OpenAPI

        :param id: The id of this AuditLog.  # noqa: E501
        :type id: int
        """
        self.openapi_types = {
            'id': int
        }

        self.attribute_map = {
            'id': 'id'
        }

        self._id = id

    @classmethod
    def from_dict(cls, dikt) -> 'AuditLog':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The AuditLog of this AuditLog.  # noqa: E501
        :rtype: AuditLog
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this AuditLog.


        :return: The id of this AuditLog.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this AuditLog.


        :param id: The id of this AuditLog.
        :type id: int
        """

        self._id = id
