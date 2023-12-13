import connexion
import six

from openapi_server.models.catalog_item import CatalogItem  # noqa: E501
from openapi_server import util


def create_catalog_item(catalog_item):  # noqa: E501
    """Create catalog item

     # noqa: E501

    :param catalog_item: 
    :type catalog_item: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        catalog_item = CatalogItem.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def list_catalog_items():  # noqa: E501
    """Lists all catalog items

     # noqa: E501


    :rtype: List[CatalogItem]
    """
    return 'do some magic!'
