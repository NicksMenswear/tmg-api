import uuid

from flask import current_app

from server.database.models import Cart, CartProduct
from server.services import NotFoundError, ServiceError
from server.services.base import BaseService


class CartService(BaseService):
    def __init__(self, session_factory, shopify_service=None):
        super().__init__(session_factory)

        self.shopify_service = shopify_service or current_app.shopify_service

    def get_cart_by_id(self, cart_id):
        with self.session_factory() as db:
            cart = db.query(Cart).filter(Cart.id == cart_id).one_or_none()

            if not cart:
                raise NotFoundError("Cart not found")

            products = cart.cart_products.all()

            cart = cart.to_dict()
            cart["products"] = [product.to_dict() for product in products]

            return cart

    def create_cart(self, **cart_data):
        with self.session_factory() as db:
            try:
                cart = Cart(
                    id=uuid.uuid4(),
                    user_id=cart_data.get("user_id"),
                    event_id=cart_data.get("event_id"),
                    attendee_id=cart_data.get("attendee_id"),
                )

                db.add(cart)

                for product in cart_data.get("products"):
                    cart_product = CartProduct(
                        id=uuid.uuid4(),
                        cart_id=cart.id,
                        product_id=product["product_id"],
                        variation_id=product["variation_id"],
                        category=product["category"],
                        quantity=product["quantity"],
                    )

                    db.add(cart_product)

                db.commit()
                db.refresh(cart)

                return cart
            except Exception as e:
                db.rollback()
                raise ServiceError("Failed to create cart", e)

    def get_cart_by_event_attendee(self, event_id, attendee_id):
        with self.session_factory() as db:
            cart = db.query(Cart).filter(Cart.event_id == event_id, Cart.attendee_id == attendee_id).one_or_none()

            if not cart:
                return "Cart not found", 204

            cart_products = db.query(CartProduct).filter(CartProduct.cart_id == cart.id).all()

            response = {
                "user_id": str(cart.user_id),
                "event_id": str(cart.event_id),
                "attendee_id": str(cart.attendee_id),
                "products": [],
            }

            for product in cart_products:
                response["products"].append(self.shopify_service.get_product_by_id(product.product_id))

            return response

    def update_cart(self, **update_cart_data):
        with self.session_factory() as db:
            cart = db.query(Cart).filter(Cart.id == update_cart_data["id"]).one_or_none()

            if not cart:
                raise NotFoundError("Cart not found")

            try:
                cart.user_id = update_cart_data.get("user_id", cart.user_id)
                cart.event_id = update_cart_data.get("event_id", cart.event_id)
                cart.attendee_id = update_cart_data.get("attendee_id", cart.attendee_id)

                existing_cart_products = db.query(CartProduct).filter(CartProduct.cart_id == cart.id).all()

                for cart_product in existing_cart_products:
                    db.delete(cart_product)

                for product in update_cart_data["products"]:
                    cart_prod_id = uuid.uuid4()
                    new_cart_product = CartProduct(
                        id=cart_prod_id,
                        cart_id=cart.id,
                        product_id=product["product_id"],
                        variation_id=product["variation_id"],
                        category=product["category"],
                        quantity=product["quantity"],
                    )

                    db.add(new_cart_product)

                db.commit()
                db.refresh(cart)
            except Exception as e:
                db.rollback()
                raise ServiceError("Failed to update cart", e)

            return cart
