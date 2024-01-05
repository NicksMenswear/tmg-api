import connexion
import six
from openapi_server.models.catalog_item import CatalogItem
from openapi_server.database.database_manager import get_database_session  # noqa: E501
from openapi_server.database.models import CatalogItem
from openapi_server import util
from werkzeug.exceptions import HTTPException
# from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
import uuid


def create_catalog_item(catalog_item):  # noqa: E501
    """Create catalog item

     # noqa: E501

    :param catalog_item: 
    :type catalog_item: dict | bytes

    :rtype: None
    """
    try:
        db = get_database_session()
        existing_product = db.query(CatalogItem).filter_by(name=catalog_item['name']).first()
        if existing_product:
            return 'Item with the same name already exists!',400
        print(catalog_item)
        catalog = CatalogItem(
            id=id,
            name=catalog_item['name'],
            price=catalog_item['price']
        )
        db.add(catalog)
        db.commit()
        db.refresh(catalog)
        return 'Product created successfully!', 201
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    finally:
        db.close()


def list_catalog_items():  # noqa: E501
    """Lists all catalog items

     # noqa: E501


    :rtype: List[CatalogItem]
    """
    try:
        db = get_database_session()
        formatted_products = []
        products = db.query(CatalogItem).all()
        for product in products:
            formatted_products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price
            }) 
        return formatted_products
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
