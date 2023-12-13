from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey,UUID 
from sqlalchemy.orm import relationship
from openapi_server.models.base_model_ import Model
from openapi_server import util

class Event(Model):
    __tablename__ = "events"

    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    # event_name = Column(String, index=True, nullable=False)
    # event_date = Column(DateTime, nullable=False)
    # user_id = Column(String, ForeignKey('users.id'), nullable=False)
    # attendees = Column(String)

    user = relationship('User', back_populates='events')

    def __init__(self, id=None, event_name=None, event_date=None, user_id=None, attendees=None):
        """Event - a model defined in OpenAPI

        :param event_name: The name of the event.
        :type event_name: str
        :param event_date: The date of the event.
        :type event_date: datetime
        :param user_id: The id of the user associated with the event.
        :type user_id: str
        :param attendees: The attendees of the event.
        :type attendees: str
        """
        self.openapi_types = {
            'id': int,
            'event_name': str,
            'event_date': str,
            'user_id': int,
            'attendees': str
        }

        self.attribute_map = {
            'id': 'id',
            'event_name': 'event_name',
            'event_date': 'event_date',
            'user_id': 'user_id',
            'attendees': 'attendees'
        }


        # super(Event, self).__init__()
        self.event_name = event_name
        self.event_date = event_date
        self.user_id = user_id
        self.attendees = attendees

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
        result['attendees'] = self.attendees
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
        if 'attendees' in values:
            self.attendees = values['attendees']

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
    def attendees(self) -> str:
        """Gets the attendees of this Event.

        :return: The attendees of this Event.
        :rtype: str
        """
        return self._attendees

    @attendees.setter
    def attendees(self, attendees: str):
        """Sets the attendees of this Event.

        :param attendees: The attendees of this Event.
        :type attendees: str
        """
        if attendees is None:
            raise ValueError("Invalid value for `attendees`, must not be `None`")  # noqa: E501

        self._attendees = attendees
