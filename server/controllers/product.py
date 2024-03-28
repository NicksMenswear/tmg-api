from server.database.database_manager import get_database_session  # noqa: E501
from server.database.models import ProductItem
import uuid
from server.controllers.hmac_1 import hmac_verification


db = get_database_session()

@hmac_verification()
def create_product_item(product_item):  # noqa: E501
    """Create product item

     # noqa: E501

    :param product_item: 
    :type product_item: dict | bytes

    :rtype: None
    """
    try:
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
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    finally:
        db.close()


@hmac_verification()
def list_product_items():  # noqa: E501
    """Lists all product items

     # noqa: E501


    :rtype: List[ProductItem]
    """
    try:
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
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    finally:
        db.close()
