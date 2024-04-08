# from server.database.database_manager import get_database_session  # noqa: E501
# from server.database.models import ProductItem
# import uuid
# from server.controllers.hmac_1 import hmac_verification


# db = get_database_session()

# @hmac_verification()
# def create_product_item(product_item):  # noqa: E501
#     """Create product item

#      # noqa: E501

#     :param product_item:
#     :type product_item: dict | bytes

#     :rtype: None
#     """
#     try:
#         existing_product = db.query(ProductItem).filter_by(name=product_item['name']).first()
#         if existing_product:
#             return 'Item with the same name already exists!',400
#         product = ProductItem(
#             id= uuid.uuid4(),
#             name=product_item['name'],
#             price=product_item['price']
#         )
#         db.add(product)
#         db.commit()
#         db.refresh(product)
#         return 'Product created successfully!', 201
#     except Exception as e:
#         db.rollback()
#         print(f"An error occurred: {e}")
#         return f"Internal Server Error : {e}", 500
#     finally:
#         db.close()


# @hmac_verification()
# def list_product_items():  # noqa: E501
#     """Lists all product items

#      # noqa: E501


#     :rtype: List[ProductItem]
#     """
#     try:
#         formatted_products = []
#         products = db.query(ProductItem).all()
#         for product in products:
#             formatted_products.append({
#                 'id': product.id,
#                 'name': product.name,
#                 'price': product.price
#             })
#         return formatted_products
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return f"Internal Server Error : {e}", 500
#     finally:
#         db.close()

############################################

from server.database.database_manager import get_database_session  # noqa: E501
from server.database.models import ProductItem
import uuid


db = get_database_session()


def create_product_item(product_item):
    # noqa: E501
    """
    Create product item

    :param product_item: Product item to create
    :type product_item: dict | bytes

    :rtype: tuple(str, int)
    """
    try:

        existing_product = db.query(ProductItem).filter_by(name=product_item["name"]).first()
        if existing_product:
            return "Item with the same name already exists!", 400

        item = ProductItem(
            id=uuid.uuid4(),
            is_active=True,
            name=product_item["name"],
            sku=product_item["SKU"],
            weight_lb=product_item["Weight"],
            height_in=product_item["Height"],
            width_in=product_item["Width"],
            length_in=product_item["Length"],
            value=product_item["Value"],
            price=product_item["Price"],
            on_hand=product_item["On_hand"],
            allocated=product_item["Allocated"],
            reserve=product_item["Reserve"],
            non_sellable_total=product_item["Non_sellable_total"],
            reorder_level=product_item["Reorder_level"],
            reorder_amount=product_item["Reorder_amount"],
            replenishment_level=product_item["Replenishment_level"],
            available=product_item["Available"],
            backorder=product_item["Backorder"],
            barcode=product_item["Barcode"],
            tags=product_item["Tags"],
        )

        db.add(item)
        db.commit()
        return "Product created successfully!", 201
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error: {e}", 500


def list_product_items():  # noqa: E501
    """Lists all product items

     # noqa: E501


    :rtype: List[ProductItem]
    """
    try:
        products = db.query(ProductItem).filter_by(is_active=True).all()

        return [product.to_dict() for product in products]
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    finally:
        db.close()


def single_product_item(product_id):  # noqa: E501
    """show single product item

    # noqa: E501
    """
    try:
        product = db.query(ProductItem).filter_by(id=product_id, is_active=True).first()
        if not product:
            return "product not found!", 200

        return product.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    finally:
        db.close()


def update_product_item(product_data):  # noqa: E501
    """update product item

    # noqa: E501
    """
    try:
        product = db.query(ProductItem).filter_by(id=product_data["id"]).first()
        if not product:
            return "product not found!", 200

        product.name = product_data["name"]
        product.sku = product_data["SKU"]
        product.weight_lb = product_data["Weight"]
        product.height_in = product_data["Height"]
        product.width_in = product_data["Width"]
        product.length_in = product_data["Length"]
        product.value = product_data["Value"]
        product.price = product_data["Price"]
        product.on_hand = product_data["On_hand"]
        product.allocated = product_data["Allocated"]
        product.reserve = product_data["Reserve"]
        product.non_sellable_total = product_data["Non_sellable_total"]
        product.reorder_level = product_data["Reorder_level"]
        product.reorder_amount = product_data["Reorder_amount"]
        product.replenishment_level = product_data["Replenishment_level"]
        product.available = product_data["Available"]
        product.backorder = product_data["Backorder"]
        product.barcode = product_data["Barcode"]
        product.tags = product_data["Tags"]

        db.commit()
        return "product details updated successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    finally:
        db.close()


def soft_delete_product(product_data):
    """Deleting product details."""
    try:
        product = db.query(ProductItem).filter_by(id=product_data["id"]).first()

        if not product:
            return "product not found", 200
        product.is_active = product_data["is_active"]
        db.commit()
        return "product deleted successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
