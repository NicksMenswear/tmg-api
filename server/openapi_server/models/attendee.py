from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey,UUID 
from sqlalchemy.orm import relationship
from models.base_model_ import Model
import util

class Attendee(Model):
    __tablename__ = "attendees"

    user = relationship('User', back_populates='attendee')

    def __init__(self, id=None, attendee_id=None, event_id=None, style=None, invite=None, pay=None, size=None, ship=None):
        """Event - a model defined in OpenAPI

        :param event_name: The name of the event.
        :type event_name: str
        :param event_date: The date of the event.
        :type event_date: datetime
        :param user_id: The id of the user associated with the event.
        :type user_id: str
        :param attendee: The attendee of the event.
        :type attendee: str
        """
        self.openapi_types = {
            'id': int,
            'attendee_id': int,
            'event_id': int,
            'style': int,
            'invite': int,
            'pay': int,
            'size': int,
            'ship': int
        }

        self.attribute_map = {
            'id': 'id',
            'attendee_id': 'attendee_id',
            'event_id': 'event_id',
            'style' : 'style',
            'invite' : 'invite',
            'pay' : 'pay',
            'size' : 'size',
            'ship' : 'ship'
        }


        # super(Event, self).__init__()
        self._id = id
        self._attendee_id = attendee_id
        self._event_id = event_id
        self._style = style
        self._invite = invite
        self._pay = pay
        self._size = size
        self._ship = ship


    @classmethod
    def from_dict(cls, dikt) -> 'Attendee':
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
        result['attendee_id'] = self.attendee_id
        result['event_id'] = self.event_id
        result['style'] = self.style
        result['invite'] = self.invite
        result['pay'] = self.pay
        result['size'] = self.size
        result['ship'] = self.ship
        return result
    
    @to_dict.setter
    def to_dict(self, values):
        """Set attributes based on a dictionary."""
        if 'id' in values:
            self.id = values['id']
        if 'attendee_id' in values:
            self.attendee_id = values['attendee_id']
        if 'event_id' in values:
            self.event_id = values['event_id']
        if 'style' in values:
            self.style = values['style']
        if 'invite' in values:
            self.invite = values['invite']
        if 'pay' in values:
            self.pay = values['pay']
        if 'size' in values:
            self.size = values['size']
        if 'ship' in values:
            self.ship = values['ship']

    @property
    def id(self) -> str:
        """Gets the id of this Event.

        :return: The id of this Event.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Event.

        :param id: The id of this Event.
        :type id: str
        """
        self._id = id


    @property
    def attendee_id(self) -> str:
        """Gets the attendee_id of this Event.

        :return: The attendee_id of this Event.
        :rtype: str
        """
        return self.attendee_id

    @attendee_id.setter
    def attendee_id(self, attendee_id: str):
        """Sets the attendee_id of this Event.

        :param attendee_id: The attendee_id of this Event.
        :type attendee_id: str
        """
        if attendee_id is None:
            raise ValueError("Invalid value for `attendee_id`, must not be `None`")  # noqa: E501

        self._attendee_id = attendee_id

    @property
    def event_id(self) -> str:
        """Gets the event_id of this Event.

        :return: The event_id of this Event.
        :rtype: str
        """
        return self._event_id

    @event_id.setter
    def event_id(self, event_id: str):
        """Sets the event_id of this Event.

        :param event_id: The event_id of this Event.
        :type event_id: str
        """
        if event_id is None:
            raise ValueError("Invalid value for `event_id`, must not be `None`")  # noqa: E501

        self._event_id = event_id

    @property
    def style(self) -> int:
        """Gets the style of this Event.

        :return: The style of this Event.
        :rtype: int
        """
        return self._style

    @style.setter
    def style(self, style: int):
        """Sets the style of this Event.

        :param style: The style of this Event.
        :type style: int
        """
        if style is None:
            raise ValueError("Invalid value for `style`, must not be `None`")  # noqa: E501

        self._style = style

    @property
    def invite(self) -> int:
        """Gets the invite of this Event.

        :return: The invite of this Event.
        :rtype: int
        """
        return self._invite

    @invite.setter
    def invite(self, invite: int):
        """Sets the invite of this Event.

        :param invite: The invite of this Event.
        :type invite: int
        """
        if invite is None:
            raise ValueError("Invalid value for `invite`, must not be `None`")  # noqa: E501

        self._invite = invite
    
    @property
    def pay(self) -> int:
        """Gets the pay of this Event.

        :return: The pay of this Event.
        :rtype: int
        """
        return self._pay

    @pay.setter
    def pay(self, pay: int):
        """Sets the pay of this Event.

        :param pay: The pay of this Event.
        :type pay: int
        """
        if pay is None:
            raise ValueError("Invalid value for `pay`, must not be `None`")  # noqa: E501

        self._pay = pay

    @property
    def size(self) -> int:
        """Gets the size of this Event.

        :return: The size of this Event.
        :rtype: int
        """
        return self._size

    @size.setter
    def size(self, size: int):
        """Sets the size of this Event.

        :param size: The size of this Event.
        :type size: int
        """
        if size is None:
            raise ValueError("Invalid value for `size`, must not be `None`")  # noqa: E501

        self._size = size

    @property
    def ship(self) -> int:
        """Gets the ship of this Event.

        :return: The ship of this Event.
        :rtype: int
        """
        return self._ship

    @ship.setter
    def ship(self, ship: int):
        """Sets the ship of this Event.

        :param ship: The ship of this Event.
        :type ship: int
        """
        if ship is None:
            raise ValueError("Invalid value for `ship`, must not be `None`")  # noqa: E501

        self._ship = ship
