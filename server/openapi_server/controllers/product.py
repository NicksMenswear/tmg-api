import connexion
import six
from openapi_server.models.product_item import ProductItem
from openapi_server.database.database_manager import get_database_session  # noqa: E501
from openapi_server.database.models import ProductItem
from openapi_server import util
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
import uuid


def create_product_item(product_item):  # noqa: E501
    """Create product item

     # noqa: E501

    :param product_item: 
    :type product_item: dict | bytes

    :rtype: None
    """
    try:
        db = get_database_session()
        existing_product = db.query(ProductItem).filter_by(name=product_item['name']).first()
        if existing_product:
            return 'Item with the same name already exists!',400
        product = ProductItem(
            id= uuid.uuid4(),
            name=product_item['name'],
            price=product_item['price']
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return 'Product created successfully!', 201
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    finally:
        db.close()


def list_product_items():  # noqa: E501
    """Lists all product items

     # noqa: E501


    :rtype: List[ProductItem]
    """
    try:
        db = get_database_session()
        formatted_products = []
        products = db.query(ProductItem).all()
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
