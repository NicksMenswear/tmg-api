import uuid
from typing import List

from server.database.database_manager import db
from server.database.models import Order, SourceType, Product, OrderItem, OrderType, StoreLocation
from server.models.order_model import OrderModel, CreateOrderModel, ProductModel
from server.services import NotFoundError, ServiceError
from server.services.user import UserService


# noinspection PyMethodMayBeStatic
class OrderService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def get_order_by_id(self, order_id: uuid.UUID) -> OrderModel:
        order = Order.query.filter(Order.id == order_id).first()

        if not order:
            raise NotFoundError("Order not found")

        order_model = OrderModel.from_orm(order)
        products = Product.query.join(OrderItem).filter(OrderItem.order_id == order_id).all()
        order_model.products = [ProductModel.from_orm(product) for product in products]

        return order_model

    def get_products_for_order(self, order_id: uuid.UUID) -> List[ProductModel]:
        return [
            ProductModel.from_orm(product)
            for product in Product.query.join(OrderItem).filter(OrderItem.order_id == order_id).all()
        ]

    def create_order(self, create_order: CreateOrderModel) -> OrderModel:
        try:
            order = Order(
                legacy_id=create_order.legacy_id,
                user_id=create_order.user_id,
                event_id=create_order.event_id,
                order_number=create_order.order_number,
                shopify_order_number=create_order.shopify_order_number,
                order_origin=SourceType(create_order.order_origin) if create_order.order_origin else None,
                order_date=create_order.order_date,
                status=create_order.status,
                shipped_date=create_order.shipped_date,
                received_date=create_order.received_date,
                ship_by_date=create_order.ship_by_date,
                shipping_method=create_order.shipping_method,
                outbound_tracking=create_order.outbound_tracking,
                store_location=StoreLocation(create_order.store_location) if create_order.store_location else None,
                order_type=[OrderType(order_type) for order_type in create_order.order_type],
                shipping_address_line1=create_order.shipping_address.line1,
                shipping_address_line2=create_order.shipping_address.line2,
                shipping_city=create_order.shipping_address.city,
                shipping_state=create_order.shipping_address.state,
                shipping_zip_code=create_order.shipping_address.zip_code,
                shipping_country=create_order.shipping_address.country,
                meta=create_order.meta,
            )
            db.session.add(order)
            db.session.flush()

            products = []

            for create_product in create_order.products:
                product = Product(
                    sku=create_product.sku,
                    name=create_product.name,
                    price=create_product.price,
                    on_hand=create_product.on_hand,
                    meta=create_product.meta,
                )
                db.session.add(product)
                db.session.flush()

                products.append(product)

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    purchased_price=product.price,
                    quantity=create_product.quantity,
                )
                db.session.add(order_item)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to create order.", e)

        created_order = OrderModel.from_orm(order)
        created_order.products = [ProductModel.from_orm(product) for product in products]

        return created_order
