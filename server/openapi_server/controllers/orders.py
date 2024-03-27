from database.models import Order, OrderItem, Event, User, ProductItem
from database.database_manager import get_database_session
import uuid
from .hmac_1 import hmac_verification



db = get_database_session()


@hmac_verification()
def create_order(order):  # noqa: E501
    """Create order

     # noqa: E501

    :param order: 
    :type order: dict | bytes

    :rtype: None
    """
    try:
        user = db.query(User).filter(User.email == order["email"]).first()
        if not user:
            return "Email not found", 204
        event = db.query(Event).filter(Event.user_id == user.id).first()
        if not event:
            return "Event not found", 204
        order_id = uuid.uuid4()
        new_order = Order(
            id = order_id,
            user_id = user.id,
            event_id = event.id,
            shipped_date = None,
            received_date = None
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        for orderitem in order['items']:
            product = db.query(ProductItem).filter(ProductItem.name == orderitem['name']).first()
            new_orderitem = OrderItem(
                id = uuid.uuid4(),
                order_id = order_id,
                product_id = product.id,
                quantity = orderitem['quantity'],
                price = product.price
            )
            db.add(new_orderitem)
            db.commit()
            db.refresh(new_orderitem)
        return 'Order created successfully!', 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def get_order_by_id(order_id):  # noqa: E501
    """Retrieve a specific order by ID

     # noqa: E501

    :param order_id: Unique identifier of the order to retrieve
    :type order_id: int

    :rtype: Order
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return 'Order not found', 204
        return order.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def get_orders(user_id=None, event_id=None):  # noqa: E501
    """Retrieve all orders, optionally filtered by user ID or event ID

     # noqa: E501

    :param user_id: Optional user ID to filter orders
    :type user_id: int
    :param event_id: Optional event ID to filter orders
    :type event_id: int

    :rtype: List[Order]
    """
    try:
        orders = db.query(Order).filter(Order.user_id==user_id, Order.event_id==event_id)
        if not orders:
            return 'Order not found', 204

        return [order.to_dict() for order in orders]
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def update_order(order):  # noqa: E501
    """Update an existing order by ID

     # noqa: E501

    :param order_id: Unique identifier of the order to update
    :type order_id: int
    :param order: 
    :type order: dict | bytes
    :rtype: None
    """
    try:
        orders = db.query(Order).filter(Order.id == order['id']).first()
        orders.shipped_date = order['shipped_date']
        orders.received_date = order['received_date']
        db.commit()
        return {"message": "Order details updated successfully"}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def delete_order(order_id):
    """ Deleting Order using id"""
    try:
        order = db.query(Order).filter(Order.id==order_id).first()
        if not order:
            return 'Order not found', 204

        order_items = db.query(OrderItem).filter(OrderItem.order_id==order.id)
        for order_item in order_items:
            db.delete(order_item)
        db.commit()

        db.delete(order)
        db.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
