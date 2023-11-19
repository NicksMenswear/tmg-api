import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.event import Event  # noqa: E501
from openapi_server import util


def create_event(event):  # noqa: E501
    """Create event

     # noqa: E501

    :param event: 
    :type event: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        event = Event.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def list_events():  # noqa: E501
    """Lists all events

     # noqa: E501


    :rtype: Union[List[Event], Tuple[List[Event], int], Tuple[List[Event], int, Dict[str, str]]
    """
    return 'do some magic!'
