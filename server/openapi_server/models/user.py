from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401
from typing import List, Dict  # noqa: F401
from models.base_model_ import Model
import util


class User(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None, first_name=None, last_name=None, email=None, shopify_id=None, temp=None, role=None):  # noqa: E501
        """User - a model defined in OpenAPI

        :param id: The id of this User.  # noqa: E501
        :type id: int
        :param first_name: The first name of this User.  # noqa: E501
        :type first_name: str
        :param last_name: The last name of this User.  # noqa: E501
        :type last_name: str
        :param email: The email of this User.  # noqa: E501
        :type email: str
        :param shopify_id: The Shopify ID of this User.  # noqa: E501
        :type shopify_id: str
        """
        self.openapi_types = {
            'id': int,
            'first_name': str,
            'last_name': str,
            'email': str,
            'shopify_id': str,
            'temp' : str,
            'role' : str
        }

        self.attribute_map = {
            'id': 'id',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'shopify_id': 'shopify_id',
            'temp' : 'temp',
            'role' : 'role'
        }

        self._id = id
        self._first_name = first_name
        self._last_name = last_name
        self._email = email
        self._shopify_id = shopify_id
        self._temp = temp
        self._role = role

    @classmethod
    def from_dict(cls, dikt) -> 'User':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The User of this User.  # noqa: E501
        :rtype: User
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this User.

        :return: The id of this User.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this User.

        :param id: The id of this User.
        :type id: int
        """
        self._id = id

    @property
    def first_name(self):
        """Gets the first name of this User.

        :return: The first name of this User.
        :rtype: str
        """
        return self._first_name

    @first_name.setter
    def first_name(self, first_name):
        """Sets the first name of this User.

        :param first_name: The first name of this User.
        :type first_name: str
        """
        if first_name is None:
            raise ValueError("Invalid value for `first_name`, must not be `None`")  # noqa: E501

        self._first_name = first_name

    @property
    def last_name(self):
        """Gets the last name of this User.

        :return: The last name of this User.
        :rtype: str
        """
        return self._last_name

    @last_name.setter
    def last_name(self, last_name):
        """Sets the last name of this User.

        :param last_name: The last name of this User.
        :type last_name: str
        """
        if last_name is None:
            raise ValueError("Invalid value for `last_name`, must not be `None`")  # noqa: E501

        self._last_name = last_name

    @property
    def email(self):
        """Gets the email of this User.

        :return: The email of this User.
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, email):
        """Sets the email of this User.

        :param email: The email of this User.
        :type email: str
        """
        if email is None:
            raise ValueError("Invalid value for `email`, must not be `None`")  # noqa: E501

        self._email = email

    @property
    def shopify_id(self):
        """Gets the Shopify ID of this User.

        :return: The Shopify ID of this User.
        :rtype: str
        """
        return self._shopify_id

    @shopify_id.setter
    def shopify_id(self, shopify_id):
        """Sets the Shopify ID of this User.

        :param shopify_id: The Shopify ID of this User.
        :type shopify_id: str
        """
        if shopify_id is None:
            raise ValueError("Invalid value for `shopify_id`, must not be `None`")  # noqa: E501

        self._shopify_id = shopify_id

    @property
    def temp(self):
        """Gets the temporary of this User.

        :return: The temporary of this User.
        :rtype: str
        """
        return self._temp

    @temp.setter
    def temp(self, temp):
        """Sets the temporary of this User.

        :param temporary: The temporary of this User.
        :type temporary: str
        """
        if temp is None:
            raise ValueError("Invalid value for `temporary`, must not be `None`")  # noqa: E501

        self._temp = temp

    @property
    def role(self):
        """Gets the role of this User.

        :return: The role of this User.
        :rtype: str
        """
        return self._role

    @role.setter
    def role(self, role):
        """Sets the role of this User.

        :param role: The role of this User.
        :type role: str
        """
        if role is None:
            raise ValueError("Invalid value for `role`, must not be `None`")  # noqa: E501

        self._role = role