from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey,UUID 
from sqlalchemy.orm import relationship
from openapi_server.models.base_model_ import Model
from openapi_server import util

class Event(Model):
    __tablename__ = "events"

    user = relationship('User', back_populates='events')

    def __init__(self, id=None, event_name=None, event_date=None, user_id=None, attendee=None, style=None, invite=None, pay=None, size=None, ship=None):
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
            'event_name': str,
            'event_date': str,
            'user_id': int,
            'attendee': str,
            'style': int,
            'invite': int,
            'pay': int,
            'size': int,
            'ship': int
        }

        self.attribute_map = {
            'id': 'id',
            'event_name': 'event_name',
            'event_date': 'event_date',
            'user_id': 'user_id',
            'attendee': 'attendee',
            'style' : 'style',
            'invite' : 'invite',
            'pay' : 'pay',
            'size' : 'size',
            'ship' : 'ship'
        }


        # super(Event, self).__init__()
        self.event_name = event_name
        self.event_date = event_date
        self.user_id = user_id
        self.attendee = attendee
        self.style = style
        self.invite = invite
        self.pay = pay
        self.size = size
        self.ship = ship


    @classmethod
    def from_dict(cls, dikt) -> 'Event':
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
        result['event_name'] = self.event_name
        result['event_date'] = self.event_date
        result['user_id'] = self.user_id
        result['attendee'] = self.attendee
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
        if 'event_name' in values:
            self.event_name = values['event_name']
        if 'event_date' in values:
            self.event_date = values['event_date']
        if 'user_id' in values:
            self.user_id = values['user_id']
        if 'attendee' in values:
            self.attendee = values['attendee']
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
    def event_name(self) -> str:
        """Gets the name of this Event.

        :return: The name of this Event.
        :rtype: str
        """
        return self._event_name

    @event_name.setter
    def event_name(self, event_name: str):
        """Sets the name of this Event.

        :param event_name: The name of this Event.
        :type event_name: str
        """
        if event_name is None:
            raise ValueError("Invalid value for `event_name`, must not be `None`")  # noqa: E501

        self._event_name = event_name

    @property
    def event_date(self) -> datetime:
        """Gets the date of this Event.

        :return: The date of this Event.
        :rtype: datetime
        """
        return self._event_date

    @event_date.setter
    def event_date(self, event_date: datetime):
        """Sets the date of this Event.

        :param event_date: The date of this Event.
        :type event_date: datetime
        """
        if event_date is None:
            raise ValueError("Invalid value for `event_date`, must not be `None`")  # noqa: E501

        self._event_date = event_date

    @property
    def user_id(self) -> str:
        """Gets the user_id of this Event.

        :return: The user_id of this Event.
        :rtype: str
        """
        return self._user_id

    @user_id.setter
    def user_id(self, user_id: str):
        """Sets the user_id of this Event.

        :param user_id: The user_id of this Event.
        :type user_id: str
        """
        if user_id is None:
            raise ValueError("Invalid value for `user_id`, must not be `None`")  # noqa: E501

        self._user_id = user_id

    @property
    def attendee(self) -> str:
        """Gets the attendee of this Event.

        :return: The attendee of this Event.
        :rtype: str
        """
        return self._attendee

    @attendee.setter
    def attendee(self, attendee: str):
        """Sets the attendee of this Event.

        :param attendee: The attendee of this Event.
        :type attendee: str
        """
        if attendee is None:
            raise ValueError("Invalid value for `attendee`, must not be `None`")  # noqa: E501

        self._attendee = attendee

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
