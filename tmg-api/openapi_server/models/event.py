from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class Event(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None, type=None, date=None):  # noqa: E501
        """Event - a model defined in OpenAPI

        :param id: The id of this Event.  # noqa: E501
        :type id: int
        :param type: The type of this Event.  # noqa: E501
        :type type: str
        :param date: The date of this Event.  # noqa: E501
        :type date: datetime
        """
        self.openapi_types = {
            'id': int,
            'type': str,
            'date': datetime
        }

        self.attribute_map = {
            'id': 'id',
            'type': 'type',
            'date': 'date'
        }

        self._id = id
        self._type = type
        self._date = date

    @classmethod
    def from_dict(cls, dikt) -> 'Event':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Event of this Event.  # noqa: E501
        :rtype: Event
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> int:
        """Gets the id of this Event.


        :return: The id of this Event.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id: int):
        """Sets the id of this Event.


        :param id: The id of this Event.
        :type id: int
        """

        self._id = id

    @property
    def type(self) -> str:
        """Gets the type of this Event.


        :return: The type of this Event.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this Event.


        :param type: The type of this Event.
        :type type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")  # noqa: E501

        self._type = type

    @property
    def date(self) -> datetime:
        """Gets the date of this Event.


        :return: The date of this Event.
        :rtype: datetime
        """
        return self._date

    @date.setter
    def date(self, date: datetime):
        """Sets the date of this Event.


        :param date: The date of this Event.
        :type date: datetime
        """
        if date is None:
            raise ValueError("Invalid value for `date`, must not be `None`")  # noqa: E501

        self._date = date
