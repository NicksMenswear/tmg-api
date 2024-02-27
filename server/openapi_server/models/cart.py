from sqlalchemy.orm import relationship
from openapi_server.models.base_model_ import Model
from openapi_server import util

class Cart(Model):
    __tablename__ = "carts"

    user = relationship('User', back_populates='carts')
    event = relationship('Event', back_populates='carts')
    attendee = relationship('Attendee', back_populates='carts')


    def __init__(self, id=None, user_id=None, event_id=None, attendee_id=None):
        """Cart - a model defined in OpenAPI

        :param user_id: The id of the user associated with the cart.
        :type user_id: str
        :param attendee: The attendee of the cart.
        :type attendee: str
        """
        self.openapi_types = {
            'id': int,
            'user_id': int,
            'event_id': int,
            'attendee_id': int,
        }

        self.attribute_map = {
            'id': 'id',
            'user_id': 'user_id',
            'event_id': 'event_id',
            'attendee_id': 'attendee_id'
        }

        # super(Cart, self).__init__()
        self._id = id
        self._user_id = user_id
        self._event_id = event_id
        self._attendee_id = attendee_id

    @classmethod
    def from_dict(cls, dikt) -> 'Cart':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Cart of this Cart.  # noqa: E501
        """
        return util.deserialize_model(dikt, cls)

    @property
    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = self.openapi_types.copy()
        result['id'] = self.id
        result['user_id'] = self.user_id
        result['event_id'] = self.event_id
        result['attendee_id'] = self.attendee_id
        return result
    
    @to_dict.setter
    def to_dict(self, values):
        """Set attributes based on a dictionary."""
        if 'id' in values:
            self.id = values['id']
        if 'user_id' in values:
            self.user_id = values['user_id']
        if 'event_id' in values:
            self.event_id = values['event_id']
        if 'attendee_id' in values:
            self.attendee_id = values['attendee_id']

    @property
    def id(self) -> str:
        """Gets the id of this Cart.

        :return: The id of this Cart.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Cart.

        :param id: The id of this Cart.
        :type id: str
        """
        self._id = id

    @property
    def user_id(self) -> str:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: str
        """
        return self._user_id

    @user_id.setter
    def user_id(self, user_id: str):
        """Sets the name of this Cart.

        :param user_id: The name of this Cart.
        :type user_id: str
        """
        if user_id is None:
            raise ValueError("Invalid value for `user_id`, must not be `None`")  # noqa: E501

        self._user_id = user_id

    @property
    def event_id(self) -> str:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: str
        """
        return self._event_id

    @event_id.setter
    def event_id(self, event_id: str):
        """Sets the name of this Cart.

        :param event_id: The name of this Cart.
        :type event_id: str
        """
        if event_id is None:
            raise ValueError("Invalid value for `event_id`, must not be `None`")  # noqa: E501

        self._event_id = event_id

    @property
    def attendee_id(self) -> str:
        """Gets the name of this Cart.

        :return: The name of this Cart.
        :rtype: str
        """
        return self._attendee_id

    @attendee_id.setter
    def attendee_id(self, attendee_id: str):
        """Sets the name of this Cart.

        :param attendee_id: The name of this Cart.
        :type attendee_id: str
        """
        if attendee_id is None:
            raise ValueError("Invalid value for `attendee_id`, must not be `None`")  # noqa: E501

        self._attendee_id = attendee_id

