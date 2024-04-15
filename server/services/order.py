import uuid

from server.database.models import Order, OrderItem
from server.services import NotFoundError, ServiceError
from server.services.base import BaseService
from server.services.event import EventService
from server.services.product import ProductService
from server.services.user import UserService


class OrderService(BaseService):
    def __init__(self, session_factory):
        super().__init__(session_factory)

        self.user_service = UserService(session_factory)
        self.event_service = EventService(session_factory)
        self.product_service = ProductService(session_factory)

    def get_order_by_id(self, order_id):
        with self.session_factory() as db:
            order = db.query(Order).filter(Order.id == order_id).first()

            if not order:
                return None

            items = self.get_order_items_by_order_id(order_id)
            enriched_order = order.to_dict()
            enriched_order["items"] = [item.to_dict() for item in items]

            return enriched_order

    def get_order_items_by_order_id(self, order_id):
        with self.session_factory() as db:
            return db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    def get_orders_by_user_and_event(self, user_id, event_id):
        with self.session_factory() as db:
            orders = db.query(Order).filter(Order.user_id == user_id, Order.event_id == event_id).all()

            enriched_orders = [order.to_dict() for order in orders]

            for enriched_order in enriched_orders:
                order_items = self.get_order_items_by_order_id(enriched_order["id"])
                enriched_order["items"] = [item.to_dict() for item in order_items]

            return enriched_orders

    def create_order(self, **order_data):
        with self.session_factory() as db:
            user = self.user_service.get_user_by_email(order_data["email"])

            if not user:
                raise NotFoundError("User not found")

            event = self.event_service.get_event_by_user_id(user.id)

            if not event:
                raise NotFoundError("Event not found")

            order_items = []

            try:
                order_id = uuid.uuid4()

                new_order = Order(
                    id=order_id, user_id=user.id, event_id=event.id, shipped_date=None, received_date=None
                )

                db.add(new_order)

                for order_item in order_data["items"]:
                    product = self.product_service.get_product_by_name(order_item["name"])

                    new_order_item = OrderItem(
                        id=uuid.uuid4(),
                        order_id=order_id,
                        product_id=product.id,
                        quantity=order_item["quantity"],
                        price=product.price,
                    )

                    order_items.append(new_order_item)

                    db.add(new_order_item)

                db.commit()
            except Exception as e:
                db.rollback()
                raise ServiceError("Failed to create order.", e)

            enriched_order = new_order.to_dict()
            enriched_order["items"] = [order_item.to_dict() for order_item in order_items]

            return enriched_order

    def update_order(self, **order_data):
        with self.session_factory() as db:
            order = db.query(Order).filter(Order.id == order_data["id"]).first()

            if not order:
                raise NotFoundError("Order not found")

            try:
                order.shipped_date = order_data["shipped_date"]
                order.received_date = order_data["received_date"]

                db.commit()
            except Exception as e:
                raise ServiceError("Failed to update order.", e)

            return order.to_dict()

    def delete_order(self, order_id):
        with self.session_factory() as db:
            order = db.query(Order).filter(Order.id == order_id).first()

            if not order:
                raise NotFoundError("Order not found")

            try:
                order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                for order_item in order_items:
                    db.delete(order_item)
                    db.commit()  # TODO: shouldn't commit here
                db.delete(order)
                db.commit()
            except Exception as e:
                db.rollback()
                raise ServiceError("Failed to delete order.", e)
