import uuid

from server.database.database_manager import db
from server.database.models import Order, OrderItem, Event
from server.services import NotFoundError, ServiceError
from server.services.event import EventService
from server.services.product import ProductService
from server.services.user import UserService


class OrderService:
    def __init__(self):
        self.user_service = UserService()
        self.event_service = EventService()
        self.product_service = ProductService()

    def get_order_by_id(self, order_id):
        order = Order.query.filter(Order.id == order_id).first()

        if not order:
            return None

        items = self.get_order_items_by_order_id(order_id)
        enriched_order = order.to_dict()
        enriched_order["items"] = [item.to_dict() for item in items]

        return enriched_order

    def get_order_items_by_order_id(self, order_id):
        return OrderItem.query.filter(OrderItem.order_id == order_id).all()

    def get_orders_by_user_and_event(self, user_id, event_id):
        orders = Order.query.filter(Order.user_id == user_id, Order.event_id == event_id).all()

        enriched_orders = [order.to_dict() for order in orders]

        for enriched_order in enriched_orders:
            order_items = self.get_order_items_by_order_id(enriched_order["id"])
            enriched_order["items"] = [item.to_dict() for item in order_items]

        return enriched_orders

    def create_order(self, order_data):
        user = self.user_service.get_user_by_email(order_data["email"])

        if not user:
            raise NotFoundError("User not found")

        # TODO: this is bug! because multiple events can be created by the same user. Debug later.
        event = Event.query.filter_by(user_id=user.id).first()

        if not event:
            raise NotFoundError("Event not found")

        order_items = []

        try:
            order_id = uuid.uuid4()

            new_order = Order(id=order_id, user_id=user.id, event_id=event.id, shipped_date=None, received_date=None)

            db.session.add(new_order)

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

                db.session.add(new_order_item)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to create order.", e)

        enriched_order = new_order.to_dict()
        enriched_order["items"] = [order_item.to_dict() for order_item in order_items]

        return enriched_order

    def update_order(self, order_data):
        order = Order.query.filter(Order.id == order_data["id"]).first()

        if not order:
            raise NotFoundError("Order not found")

        try:
            order.shipped_date = order_data["shipped_date"]
            order.received_date = order_data["received_date"]

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to update order.", e)

        return order.to_dict()

    def delete_order(self, order_id):
        order = Order.query.filter(Order.id == order_id).first()

        if not order:
            raise NotFoundError("Order not found")

        try:
            order_items = OrderItem.query.filter(OrderItem.order_id == order.id).all()
            for order_item in order_items:
                db.session.delete(order_item)
                db.session.commit()  # TODO: shouldn't commit here
            db.session.delete(order)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to delete order.", e)
