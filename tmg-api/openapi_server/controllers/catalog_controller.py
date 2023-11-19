import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.catalog_item import CatalogItem  # noqa: E501
from openapi_server import util


def create_catalog_item(catalog_item):  # noqa: E501
    """Create catalog item

     # noqa: E501

    :param catalog_item: 
    :type catalog_item: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        catalog_item = CatalogItem.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def list_catalog_items():  # noqa: E501
    """Lists all catalog items

     # noqa: E501


    :rtype: Union[List[CatalogItem], Tuple[List[CatalogItem], int], Tuple[List[CatalogItem], int, Dict[str, str]]
    """
    return 'do some magic!'
