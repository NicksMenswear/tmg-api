import logging
import random
import string
import time
import uuid
from datetime import datetime, timedelta
from typing import List

from server.database.database_manager import db
from server.database.models import Order, SourceType, Product, OrderItem, OrderType
from server.models.measurement_model import MeasurementModel
from server.models.order_model import OrderModel, CreateOrderModel, ProductModel
from server.models.size_model import SizeModel
from server.services import NotFoundError, ServiceError
from server.services.measurement_service import MeasurementService
from server.services.sku_builder_service import SkuBuilder
from server.services.user_service import UserService

ORDER_STATUS_READY = "ORDER_READY"
ORDER_STATUS_PENDING_MEASUREMENTS = "ORDER_PENDING_MEASUREMENTS"
ORDER_STATUS_PENDING_MISSING_SKU = "ORDER_PENDING_MISSING_SKU"
MAX_DAYS_TO_LOOK_UP_FOR_PENDING_MEASUREMENTS_IN_JOB = 60
MAX_DAYS_TO_LOOK_UP_FOR_PENDING_MEASUREMENTS_FOR_USER = 365

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class OrderService:
    def __init__(self, user_service: UserService, measurement_service: MeasurementService, sku_builder: SkuBuilder):
        self.user_service = user_service
        self.measurement_service = measurement_service
        self.sku_builder = sku_builder

    def generate_order_number(self):
        prefix = "MG"

        timestamp = time.strftime("%y%m%d%H%M%S")
        random_string_length = 4
        random_string = "".join(random.choices(string.ascii_uppercase + string.digits, k=random_string_length))
        new_order_number = f"{prefix}{timestamp}{random_string}"

        return new_order_number

    def get_order_by_id(self, order_id: uuid.UUID) -> OrderModel:
        order = Order.query.filter(Order.id == order_id).first()

        if not order:
            raise NotFoundError("Order not found")

        order_model = OrderModel.from_orm(order)
        products = Product.query.join(OrderItem).filter(OrderItem.order_id == order_id).all()
        order_model.products = [ProductModel.from_orm(product) for product in products]

        return order_model

    def get_product_by_id(self, product_id: uuid.UUID) -> ProductModel:
        product = Product.query.filter(Product.id == product_id).first()

        if not product:
            raise NotFoundError("Product not found")

        return ProductModel.from_orm(product)

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
                shopify_order_id=create_order.shopify_order_id,
                shopify_order_number=create_order.shopify_order_number,
                order_origin=SourceType(create_order.order_origin) if create_order.order_origin else None,
                order_date=create_order.order_date,
                status=create_order.status,
                shipped_date=create_order.shipped_date,
                received_date=create_order.received_date,
                ship_by_date=create_order.ship_by_date,
                shipping_method=create_order.shipping_method,
                outbound_tracking=create_order.outbound_tracking,
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
                    shopify_sku=create_product.shopify_sku,
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

    def get_orders_by_status_and_not_older_then_days(
        self, status: str, days: int, user_id: uuid.UUID = None
    ) -> List[OrderModel]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = Order.query.filter(Order.status == status).filter(Order.created_at >= cutoff_date)

        if user_id:
            query = query.filter(Order.user_id == user_id)

        orders = query.all()

        return [OrderModel.from_orm(order) for order in orders]

    def update_sku_for_product(self, product_id: uuid.UUID, sku: str) -> ProductModel:
        try:
            product = Product.query.filter(Product.id == product_id).first()
            product.sku = sku

            db.session.commit()
            db.session.refresh(product)
        except Exception as e:
            raise ServiceError("Failed to update SKU for product.", e)

        return ProductModel.from_orm(product)

    def update_order_status(self, order_id: uuid.UUID, status: str) -> OrderModel:
        try:
            order = Order.query.filter(Order.id == order_id).first()
            order.status = status

            db.session.commit()
            db.session.refresh(order)
        except Exception as e:
            raise ServiceError("Failed to update order status.", e)

        return OrderModel.from_orm(order)

    def update_user_pending_orders_with_latest_measurements(self, size_model: SizeModel):
        measurement_model = self.measurement_service.get_latest_measurement_for_user(size_model.user_id)

        orders = self.get_orders_by_status_and_not_older_then_days(
            ORDER_STATUS_PENDING_MEASUREMENTS, MAX_DAYS_TO_LOOK_UP_FOR_PENDING_MEASUREMENTS_FOR_USER
        )

        for order in orders:
            order.products = self.get_products_for_order(order.id)  # TODO: Do something smarter later
            self.update_order_skus_according_to_measurements(order, size_model, measurement_model)

    def update_order_skus_according_to_measurements(
        self, order: OrderModel, size_model: SizeModel, measurement_model: MeasurementModel
    ) -> OrderModel:
        if order.status != ORDER_STATUS_PENDING_MEASUREMENTS:
            raise ServiceError("Order is not in pending measurements status")

        if not size_model or not measurement_model:
            raise ServiceError("Size or measurement model is missing")

        if not order.products:
            return order

        num_products = len(order.products)
        num_products_with_sku = 0

        for product in order.products:
            if not product.shopify_sku:
                logger.error(f"Product {product.id} is missing shopify SKU")
                continue

            current_shiphero_sku = product.sku

            try:
                new_shiphero_sku = self.sku_builder.build(product.shopify_sku, size_model, measurement_model)
            except ServiceError as e:
                logger.error(
                    f"Failed to build SKU for product with shopify sku {product.shopify_sku} in order {order.order_number}. Sizing model id: {size_model.id}. Measurement model id: {measurement_model.id}. Error: {e}"
                )
                new_shiphero_sku = None

            if current_shiphero_sku:
                if current_shiphero_sku == new_shiphero_sku:
                    num_products_with_sku += 1
                else:
                    logger.error(
                        f"SKU mismatch for product {product.id} in order {order.order_number}: current SKU {current_shiphero_sku}, new SKU {new_shiphero_sku}. Taking new SKU {new_shiphero_sku}"
                    )
                    self.update_sku_for_product(product.id, new_shiphero_sku)
                    num_products_with_sku += 1
            else:
                if new_shiphero_sku:
                    num_products_with_sku += 1
                    self.update_sku_for_product(product.id, new_shiphero_sku)
                else:
                    pass

        if num_products_with_sku == num_products:
            return self.update_order_status(order.id, ORDER_STATUS_READY)
        else:
            return self.update_order_status(order.id, ORDER_STATUS_PENDING_MISSING_SKU)
