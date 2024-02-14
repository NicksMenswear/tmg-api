from openapi_server.models.base_model_ import Model
from openapi_server import util

class Look(Model):
    __tablename__ = "looks"


    def __init__(self, id=None, look_name=None, user_id=None, product_specs=None):
        """Look - a model defined in OpenAPI

        :param look_name: The name of the look.
        :param product_specs: The details of the product_specs.
        """
        self.openapi_types = {
            'id': int,
            'look_name': str,
            'user_id': str,
            'product_specs': str
        }

        self.attribute_map = {
            'id': 'id',
            'look_name': 'look_name',
            'user_id': 'user_id',
            'product_specs': 'product_specs'
        }


        self._id = id
        self._look_name = look_name
        self._user_id = user_id
        self._product_specs = product_specs

    @classmethod
    def from_dict(cls, dikt) -> 'Look':
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
        result['look_name'] = self.look_name
        result['useer_id'] = self.user_id
        result['product_specs'] = self.product_specs
        return result
    
    @to_dict.setter
    def to_dict(self, values):
        """Set attributes based on a dictionary."""
        if 'id' in values:
            self.id = values['id']
        if 'look_name' in values:
            self.look_name = values['look_name']
        if 'user_id' in values:
            self.user_id = values['user_id']
        if 'product_specs' in values:
            self.product_specs = values['product_specs']

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
    def look_name(self) -> str:
        """Gets the name of this Look.

        :return: The name of this Look.
        :rtype: str
        """
        return self._look_name

    @look_name.setter
    def look_name(self, look_name: str):
        """Sets the name of this Look.

        :param look_name: The name of this Look.
        :type look_name: str
        """
        if look_name is None:
            raise ValueError("Invalid value for `look_name`, must not be `None`")  # noqa: E501

        self._look_name = look_name

    @property
    def user_id(self):
        """Gets the user_id of this Look.


        :return: The user_id of this Look.
        :rtype: int
        """
        return self._user_id

    @user_id.setter
    def user_id(self, user_id):
        """Sets the user_id of this Look.


        :param user_id: The user_id of this Look.
        :type user_id: int
        """
        if user_id is None:
            raise ValueError("Invalid value for `user_id`, must not be `None`")  # noqa: E501

        self._user_id = user_id

    @property
    def product_specs(self) -> str:
        """Gets the specs of this Look.

        :return: The specs of this Look.
        :rtype: string
        """
        return self._product_specs

    @product_specs.setter
    def product_specs(self, product_specs: str):
        """Sets the specs of this Look.

        :param specs: The date of this Look.
        :type specs: string
        """
        if product_specs is None:
            raise ValueError("Invalid value for `product_specs`, must not be `None`")  # noqa: E501

        self._product_specs = product_specs
    