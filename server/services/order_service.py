import logging
import random
import string
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select

from server.database.database_manager import db
from server.database.models import Order, SourceType, Product, OrderItem, OrderType, Address
from server.models.measurement_model import MeasurementModel
from server.models.order_model import OrderModel, CreateOrderModel, CreateOrderItemModel, OrderItemModel
from server.models.product_model import ProductModel
from server.models.size_model import SizeModel
from server.services import NotFoundError, ServiceError
from server.services.measurement_service import MeasurementService
from server.services.product_service import ProductService
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
    def __init__(
        self,
        user_service: UserService,
        product_service: Optional[ProductService] = None,
        measurement_service: Optional[MeasurementService] = None,
        sku_builder: Optional[SkuBuilder] = None,
    ):
        self.user_service = user_service
        self.product_service = product_service
        self.measurement_service = measurement_service
        self.sku_builder = sku_builder

    def generate_order_number(self) -> str:
        prefix = "MG"

        timestamp = time.strftime("%y%m%d%H%M%S")
        random_string_length = 4
        random_string = "".join(random.choices(string.ascii_uppercase + string.digits, k=random_string_length))
        new_order_number = f"{prefix}{timestamp}{random_string}"

        return new_order_number

    def get_order_by_id(self, order_id: uuid.UUID) -> OrderModel:
        order = db.session.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()

        if not order:
            raise NotFoundError("Order not found")

        order_model = OrderModel.model_validate(order)
        products = (
            db.session.execute(select(Product).join(OrderItem).where(OrderItem.order_id == order_id)).scalars().all()
        )
        order_model.products = [ProductModel.model_validate(product) for product in products]

        return order_model

    def get_order_by_shopify_id(self, shopify_order_id: uuid.UUID) -> OrderModel:
        order = Order.query.filter(Order.shopify_order_id == shopify_order_id).first()

        if not order:
            raise NotFoundError("Order not found")

        return OrderModel.model_validate(order)

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
                shipping_address_line1=create_order.shipping_address.line1 if create_order.shipping_address else None,
                shipping_address_line2=create_order.shipping_address.line2 if create_order.shipping_address else None,
                shipping_city=create_order.shipping_address.city if create_order.shipping_address else None,
                shipping_state=create_order.shipping_address.state if create_order.shipping_address else None,
                shipping_zip_code=create_order.shipping_address.zip_code if create_order.shipping_address else None,
                shipping_country=create_order.shipping_address.country if create_order.shipping_address else None,
                meta=create_order.meta,
            )
            db.session.add(order)
            if create_order.shipping_address:
                address = Address(
                    user_id=create_order.user_id,
                    address_type="shipping",
                    address_line1=create_order.shipping_address.line1,
                    address_line2=create_order.shipping_address.line2,
                    city=create_order.shipping_address.city,
                    state=create_order.shipping_address.state,
                    zip_code=create_order.shipping_address.zip_code,
                    country=create_order.shipping_address.country,
                )
                db.session.add(address)
            db.session.commit()
            db.session.refresh(order)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to create order.", e)

        return OrderModel.model_validate(order)

    def update_order(self, update_order: OrderModel) -> OrderModel:
        order = Order.query.filter(Order.id == update_order.id).first()

        if not order:
            raise NotFoundError("Order not found")

        try:
            order.legacy_id = (update_order.legacy_id,)
            order.user_id = (update_order.user_id,)
            order.event_id = (update_order.event_id,)
            order.order_number = (update_order.order_number,)
            order.shopify_order_id = (update_order.shopify_order_id,)
            order.shopify_order_number = (update_order.shopify_order_number,)
            order.order_origin = (SourceType(update_order.order_origin) if update_order.order_origin else None,)
            order.order_date = (update_order.order_date,)
            order.status = (update_order.status,)
            order.shipped_date = (update_order.shipped_date,)
            order.received_date = (update_order.received_date,)
            order.ship_by_date = (update_order.ship_by_date,)
            order.shipping_method = (update_order.shipping_method,)
            order.outbound_tracking = (update_order.outbound_tracking,)
            order.order_type = ([OrderType(order_type) for order_type in update_order.order_type],)
            order.shipping_address_line1 = (
                update_order.shipping_address.line1 if update_order.shipping_address else None,
            )
            order.shipping_address_line2 = (
                update_order.shipping_address.line2 if update_order.shipping_address else None,
            )
            order.shipping_city = (update_order.shipping_address.city if update_order.shipping_address else None,)
            order.shipping_state = (update_order.shipping_address.state if update_order.shipping_address else None,)
            order.shipping_zip_code = (
                update_order.shipping_address.zip_code if update_order.shipping_address else None,
            )
            order.shipping_country = (update_order.shipping_address.country if update_order.shipping_address else None,)
            order.meta = (update_order.meta,)

            db.session.commit()
            db.session.refresh(order)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to update order.", e)

        return OrderModel.model_validate(order)

    def create_order_item(self, create_order_item: CreateOrderItemModel) -> OrderItemModel:
        try:
            order_item = OrderItem(
                order_id=create_order_item.order_id,
                product_id=create_order_item.product_id,
                shopify_sku=create_order_item.shopify_sku,
                purchased_price=create_order_item.purchased_price,
                quantity=create_order_item.quantity,
            )
            db.session.add(order_item)
            db.session.commit()
            db.session.refresh(order_item)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to create order.", e)

        return OrderItemModel.model_validate(order_item)

    def get_order_items_by_order_id(self, order_id: uuid.UUID) -> List[OrderItemModel]:
        order_items = db.session.execute(select(OrderItem).where(OrderItem.order_id == order_id)).scalars().all()

        return [OrderItemModel.model_validate(order_item) for order_item in order_items]

    def get_orders_by_status_and_not_older_then_days(
        self, status: str, days: int, user_id: uuid.UUID = None
    ) -> List[OrderModel]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = select(Order).where(Order.status == status).where(Order.created_at >= cutoff_date)

        if user_id:
            query = query.where(Order.user_id == user_id)

        orders = db.session.execute(query).scalars().all()

        return [OrderModel.model_validate(order) for order in orders]

    def update_order_status(
        self,
        order_id: uuid.UUID,
        status: str,
        sizing_model: Optional[SizeModel] = None,
        measurement_model: Optional[MeasurementModel] = None,
    ) -> OrderModel:
        try:
            order = db.session.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
            order.status = status

            if order.meta is None:
                order.meta = {}

            if not order.meta.get("sizes_id") and sizing_model is not None:
                meta_clone = order.meta.copy()
                meta_clone["sizes_id"] = str(sizing_model.id)
                meta_clone["measurements_id"] = str(measurement_model.id)
                order.meta = meta_clone

            db.session.commit()
            db.session.refresh(order)
        except Exception as e:
            raise ServiceError("Failed to update order status.", e)

        return OrderModel.model_validate(order)

    def update_user_pending_orders_with_latest_measurements(self, size_model: SizeModel):
        measurement_model = self.measurement_service.get_latest_measurement_for_user(size_model.user_id)

        orders = self.get_orders_by_status_and_not_older_then_days(
            ORDER_STATUS_PENDING_MEASUREMENTS, MAX_DAYS_TO_LOOK_UP_FOR_PENDING_MEASUREMENTS_FOR_USER, size_model.user_id
        )

        for order in orders:
            order.products = self.product_service.get_products_for_order(order.id)  # TODO: Do something smarter later
            self.update_order_skus_according_to_measurements(order, size_model, measurement_model)

    def associate_order_item_with_product(self, order_item_id: uuid.UUID, product_id: uuid.UUID):
        try:
            order_item = db.session.execute(select(OrderItem).where(OrderItem.id == order_item_id)).scalar_one_or_none()
            order_item.product_id = product_id

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to associate order item with product.")

    def update_order_skus_according_to_measurements(
        self, order: OrderModel, size_model: SizeModel, measurement_model: MeasurementModel
    ) -> OrderModel:
        if order.status != ORDER_STATUS_PENDING_MEASUREMENTS:
            raise ServiceError("Order is not in pending measurements status")

        if not size_model or not measurement_model:
            raise ServiceError("Size or measurement model is missing")

        order_items = self.get_order_items_by_order_id(order.id)

        if not order_items:
            return order

        num_order_items = len(order_items)
        num_products = 0

        for order_item in order_items:
            if not order_item.shopify_sku:
                logger.error(
                    f"Order item {order_item.id} is missing shopify SKU for order {order.order_number} / {order.id} / {order.shopify_order_id}"
                )
                continue

            current_shiphero_sku = None

            if order_item.product_id:
                product = self.product_service.get_product_by_id(order_item.product_id)
                current_shiphero_sku = product.sku

            try:
                new_shiphero_sku = self.sku_builder.build(order_item.shopify_sku, size_model, measurement_model)
            except ServiceError as e:
                logger.error(
                    f"Failed to build SKU for product with shopify sku {order_item.shopify_sku} in order {order.order_number}. Sizing model id: {size_model.id}. Measurement model id: {measurement_model.id}. Error: {e}"
                )
                new_shiphero_sku = None

            if current_shiphero_sku:
                if current_shiphero_sku == new_shiphero_sku:
                    num_products += 1
                else:
                    logger.error(
                        f"SKU mismatch for product {order_item.id} in order {order.order_number}: current SKU {current_shiphero_sku}, new SKU {new_shiphero_sku}. Taking new SKU {new_shiphero_sku}"
                    )
                    product = self.product_service.get_product_by_sku(new_shiphero_sku)
                    num_products += 1
                    self.associate_order_item_with_product(order_item.id, product.id)
            else:
                if new_shiphero_sku:
                    num_products += 1
                    product = self.product_service.get_product_by_sku(new_shiphero_sku)
                    self.associate_order_item_with_product(order_item.id, product.id)
                else:
                    pass

        if num_products == num_order_items:
            return self.update_order_status(order.id, ORDER_STATUS_READY, size_model, measurement_model)
        else:
            return self.update_order_status(order.id, ORDER_STATUS_PENDING_MISSING_SKU, size_model, measurement_model)
