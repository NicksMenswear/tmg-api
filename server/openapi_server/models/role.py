from openapi_server.models.base_model_ import Model
from openapi_server import util

class Role(Model):
    __tablename__ = "roles"


    def __init__(self, id=None, role_name=None, event_id=None, look_id=None):
        """Role - a model defined in OpenAPI

        :param role_name: The name of the role.
        :param event_id: The details of the event_id.
        :param look_id: The details of the look_id.
        """
        self.openapi_types = {
            'id': int,
            'role_name': str,
            'event_id': str,
            'look_id': str
        }

        self.attribute_map = {
            'id': 'id',
            'role_name': 'role_name',
            'event_id': 'event_id',
            'look_id': 'look_id'
        }


        self._id = id
        self._role_name = role_name
        self._event_id = event_id
        self._look_id = look_id

    @classmethod
    def from_dict(cls, dikt) -> 'Role':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Event of this Event.  # noqa: E501
        """
        return util.deserialize_model(dikt, cls)

    @property
    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = self.openapi_types.copy()
        result['id'] = self.id
        result['role_name'] = self.role_name
        result['product_specs'] = self.product_specs
        return result
    
    @to_dict.setter
    def to_dict(self, values):
        """Set attributes based on a dictionary."""
        if 'id' in values:
            self.id = values['id']
        if 'role_name' in values:
            self.role_name = values['role_name']
        if 'event_id' in values:
            self.event_id = values['event_id']
        if 'look_id' in values:
            self.look_id = values['look_id']

    @property
    def id(self) -> str:
        """Gets the id of this Look.

        :return: The id of this Look.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Look.

        :param id: The id of this Look.
        :type id: str
        """
        self._id = id

    @property
    def role_name(self) -> str:
        """Gets the name of this Look.

        :return: The name of this Look.
        :rtype: str
        """
        return self._role_name

    @role_name.setter
    def role_name(self, role_name: str):
        """Sets the name of this Look.

        :param role_name: The name of this Look.
        :type role_name: str
        """
        if role_name is None:
            raise ValueError("Invalid value for `role_name`, must not be `None`")  # noqa: E501

        self._role_name = role_name


    @property
    def event_id(self):
        """Gets the event_id of this Role.


        :return: The event_id of this Role.
        :rtype: int
        """
        return self._event_id

    @event_id.setter
    def event_id(self, event_id):
        """Sets the event_id of this Role.


        :param event_id: The event_id of this Role.
        :type event_id: int
        """
        if event_id is None:
            raise ValueError("Invalid value for `event_id`, must not be `None`")  # noqa: E501

        self._event_id = event_id


    @property
    def look_id(self):
        """Gets the look_id of this Role.


        :return: The look_id of this Role.
        :rtype: int
        """
        return self._look_id

    @look_id.setter
    def look_id(self, look_id):
        """Sets the look_id of this Role.


        :param look_id: The look_id of this Role.
        :type look_id: int
        """
        if look_id is None:
            raise ValueError("Invalid value for `look_id`, must not be `None`")  # noqa: E501

        self._look_id = look_id
