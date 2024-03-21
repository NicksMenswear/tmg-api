from openapi_server.database.models import Cart, CartProduct
from openapi_server.database.database_manager import get_database_session
from .cart_data_extractor import *
from werkzeug.exceptions import HTTPException
from .shopify import *
import uuid
import os
from .hmac_1 import hmac_verification


shopify_store = os.getenv('shopify_store')
admin_api_access_token = os.getenv('admin_api_access_token')

db = get_database_session()

@hmac_verification()
def create_cart(cart):  
    """Create cart

    :param cart: 
    :type cart: dict | bytes
    :rtype: None
    """
    try:
        cart_id = uuid.uuid4()
        if 'user_id' not in cart:
            cart['user_id'] = None
        new_cart = Cart(
            id=cart_id,
            user_id=cart['user_id'],
            event_id=cart['event_id'],
            attendee_id=cart['attendee_id']
        )
        db.add(new_cart)

        if 'products' in cart:
            for product in cart['products']:
                cart_prod_id = uuid.uuid4()
                new_cart_product = CartProduct(
                    id = cart_prod_id,
                    cart_id=cart_id,
                    product_id=product['product_id'],
                    variation_id=product['variation_id'],
                    category=product['category'],
                    quantity=product['quantity']
                )
                db.add(new_cart_product)
        
        db.commit()
        # return 'Cart created successfully!', 201
        return cart_id
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def get_cart_by_id(cart_id):  # noqa: E501
    """Retrieve a specific cart by ID

     # noqa: E501

    :param cart_id: Unique identifier of the cart to retrieve
    :type cart_id: int

    :rtype: cart
    """
    try:
        cart = db.query(Cart).filter(Cart.id == cart_id).first()
        if not cart:
            return 'Cart not found', 204
        cart_products = db.query(CartProduct).filter(CartProduct.cart_id == cart_id).all()
        response = {
            "user_id": str(cart.user_id),
            "event_id": str(cart.event_id),
            "attendee_id": str(cart.attendee_id),
            "products": []
        }

        for product in cart_products:

            response["products"].append({
                "product_id": str(product.product_id),
                "variation_id": str(product.variation_id),
                "category": product.category,
                "quantity": product.quantity
            })

        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def get_cart_by_event_attendee(event_id,attendee_id):  # noqa: E501
    """Retrieve a specific cart by ID

     # noqa: E501

    :param cart_id: Unique identifier of the cart to retrieve
    :type cart_id: int

    :rtype: cart
    """
    try:
        cart = db.query(Cart).filter(Cart.event_id == event_id, Cart.attendee_id == attendee_id).first()
        if not cart:
            return 'Cart not found', 204
        cart_products = db.query(CartProduct).filter(CartProduct.cart_id == cart.id).all()
        response = {
            "user_id": str(cart.user_id),
            "event_id": str(cart.event_id),
            "attendee_id": str(cart.attendee_id),
            "products": []
        }
        for product in cart_products:
            url = f"https://{shopify_store}.myshopify.com/admin/api/2024-01/products/{product.product_id}.json"
            headers = {
                'Content-Type': 'application/json',
                'X-Shopify-Access-Token': admin_api_access_token,
            }
            prod_response = requests.get(url, headers=headers)
            data = None
            if prod_response.status_code == 200:
                prod_response = prod_response.json()
                data = data_extractor(prod_response, product.variation_id)
            else:
                data = "Not Found"
            response["products"].append({
                "product_id": str(product.product_id),
                "variation_id": str(product.variation_id),
                "category": product.category,
                "quantity": product.quantity,
                "Product_details" : [data]
            })

        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def update_cart(cart):  # noqa: E501
    """Update an existing cart by ID

     # noqa: E501

    :param cart_id: Unique identifier of the cart to update
    :type cart_id: int
    :param cart: 
    :type cart: dict | bytes
    :rtype: None
    """
    try:
        cart_id = cart['id']
        user_id = cart.get('user_id', None)
        event_id = cart.get('event_id')
        attendee_id = cart.get('attendee_id')

        existing_cart = db.query(Cart).filter(Cart.id == cart_id).first()

        if existing_cart:
            existing_cart.user_id = user_id
            existing_cart.event_id = event_id
            existing_cart.attendee_id = attendee_id

            db.commit()

            if 'products' in cart:
                existing_cart_products = db.query(CartProduct).filter(CartProduct.cart_id == cart_id).all()

                for cart_product in existing_cart_products:
                    db.delete(cart_product)

                for product in cart['products']:
                    cart_prod_id = uuid.uuid4()
                    new_cart_product = CartProduct(
                        id=cart_prod_id,
                        cart_id=cart_id,
                        product_id=product['product_id'],
                        variation_id=product['variation_id'],
                        category=product['category'],
                        quantity=product['quantity']
                    )
                    db.add(new_cart_product)

                db.commit()
            return 'Cart updated successfully', 200
        else:
            return 'Cart not found', 404

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
