import logging
import uuid
from typing import List

from sqlalchemy import func

from server.database.database_manager import db
from server.database.models import (
    User,
    Attendee,
    Discount,
    Look,
    Event,
    Order,
    OrderItem,
    Role,
    Size,
    Measurement,
    Address,
)
from server.services import ServiceError
from server.services.integrations.shopify_service import AbstractShopifyService

logger = logging.getLogger(__name__)

NUMBER_OF_USERS_TO_PROCESS = 20

SYSTEM_E2E_EMAILS_TO_KEEP = {
    "e2e+01@mail.dev.tmgcorp.net",
    "e2e+02@mail.dev.tmgcorp.net",
    "e2e+03@mail.dev.tmgcorp.net",
    "e2e+04@mail.dev.tmgcorp.net",
    "e2e+05@mail.dev.tmgcorp.net",
}

# CUSTOMER_EMAIL_MATCHING_PATTERN = "*@example.com"
# CUSTOMER_EMAIL_MATCHING_PATTERN = "e2etmg*@hotmail.com"
CUSTOMER_EMAIL_MATCHING_PATTERN = "automation*@themoderngroom.com"
# CUSTOMER_EMAIL_MATCHING_PATTERN = "e2e+*@mail.dev.tmgcorp.net"


class E2ECleanUpService:
    def __init__(self, shopify_service: AbstractShopifyService):
        self.shopify_service = shopify_service

    def cleanup(self) -> None:
        customers = self.shopify_service.get_customers_by_email_pattern(
            CUSTOMER_EMAIL_MATCHING_PATTERN, NUMBER_OF_USERS_TO_PROCESS
        )

        for customer in customers:
            email = customer.get("email")
            customer_shopify_id = customer.get("id")

            if not email:
                continue

            is_system_user = email in SYSTEM_E2E_EMAILS_TO_KEEP

            if is_system_user:
                logger.info(f"Skipping system user: {email}")
                continue

            logger.info(f"Processing customer: {email}")

            try:
                user = self.__get_user_by_email(email)

                if not user:
                    logger.error(f"User not found in db by email: {email}")

                    self.__delete_shopify_customer(customer_shopify_id)

                    continue

                attendees = self.__get_attendees(user.id)

                for attendee in attendees:
                    discounts = self.__get_discounts(attendee.id)

                    for discount in discounts:
                        discount_code = discount.shopify_discount_code

                        logger.info(f"Deleting discount: {discount_code}")

                        if discount.shopify_discount_code_id and discount_code:
                            self.__delete_shopify_discount(discount.shopify_discount_code_id)

                        self.__delete_discount(discount.id)
                    self.__delete_attendee(attendee.id)

                events = self.__get_events(user.id)
                has_hanging_events = False

                for event in events:
                    num_attendees = self.__num_attendees_in_event(event.id)

                    logger.info(f"Deleting event: {event.id}")

                    if num_attendees > 0:
                        has_hanging_events = True
                        logger.info(f"Event has attendees, skipping deletion: {event.id}")
                        continue

                    self.__delete_roles(event.id)

                    orders = self.__get_orders_for_event(event.id)

                    for order in orders:
                        logger.info(f"Deleting order: {order.id}")
                        self.__delete_order_items_for_order(order.id)
                        self.__delete_order(order.id)

                    self.__delete_event(event.id)

                    db.session.commit()

                if has_hanging_events:
                    db.session.commit()

                    continue

                self.__delete_sizes(user.id)
                self.__delete_measurements(user.id)
                self.__delete_addresses(user.id)

                looks = self.__get_user_looks(user.id)

                for look in looks:
                    product_specs = look.product_specs

                    if product_specs and product_specs.get("bundle", {}).get("product_id"):
                        shopify_bundle_product_id = product_specs["bundle"]["product_id"]

                        self.__delete_shopify_product(shopify_bundle_product_id)

                        for item in product_specs.get("items", []):
                            if not item.get("variant_sku", "").startswith("bundle-"):
                                continue

                            self.__delete_shopify_product(item.get("product_id"))

                    self.__delete_look(look.id)

                if is_system_user:
                    db.session.commit()
                    continue

                logger.info(f"Deleting customer: {email}")

                self.__delete_shopify_customer(customer_shopify_id)
                self.__delete_user(user.id)

                db.session.commit()
            except Exception:
                db.session.rollback()
                logger.exception(f"Failed to process customer: {email}")

    def __delete_shopify_customer(self, shopify_customer_id: str) -> None:
        try:
            self.shopify_service.delete_customer(shopify_customer_id)
        except ServiceError:
            logger.error(f"Failed to delete customer from shopify: {shopify_customer_id}")

    def __delete_shopify_product(self, product_id: int) -> None:
        try:
            self.shopify_service.delete_product(product_id)
        except ServiceError:
            logger.exception(f"Failed to delete product from shopify: {product_id}")

    def __delete_shopify_discount(self, discount_id: int) -> None:
        try:
            self.shopify_service.delete_discount(discount_id)
        except ServiceError:
            logger.error(f"Failed to delete discount from shopify: {discount_id}")

    @staticmethod
    def __num_attendees_in_event(event_id: uuid.UUID) -> int:
        return Attendee.query.filter(Attendee.event_id == event_id).count()

    @staticmethod
    def __get_user_by_email(email: str) -> User:
        return User.query.filter(func.lower(User.email) == email.lower()).first()

    @staticmethod
    def __get_events(user_id: uuid.UUID) -> List[Attendee]:
        return Event.query.filter(Event.user_id == user_id).all()

    @staticmethod
    def __get_attendees(user_id: uuid.UUID) -> List[Attendee]:
        return Attendee.query.filter(Attendee.user_id == user_id).all()

    @staticmethod
    def __get_attendees_with_look(look_id: uuid.UUID) -> List[Attendee]:
        return Attendee.query.filter(Attendee.look_id == look_id).all()

    @staticmethod
    def __delete_discount(discount_id: uuid.UUID) -> None:
        Discount.query.filter(Discount.id == discount_id).delete()

    @staticmethod
    def __delete_look(look_id: uuid.UUID) -> None:
        Look.query.filter(Look.id == look_id).delete()

    @staticmethod
    def __delete_attendee(attendee_id: uuid.UUID) -> None:
        Attendee.query.filter(Attendee.id == attendee_id).delete()

    @staticmethod
    def __get_discounts(attendee_id: uuid.UUID) -> List[Discount]:
        return Discount.query.filter(Discount.attendee_id == attendee_id).all()

    @staticmethod
    def __get_user_looks(user_id: uuid.UUID) -> List[Look]:
        return Look.query.filter(Look.user_id == user_id).all()

    @staticmethod
    def __get_orders_for_event(event_id: uuid.UUID) -> List[Order]:
        return Order.query.filter(Order.event_id == event_id).all()

    @staticmethod
    def __delete_order_items_for_order(order_id: uuid.UUID) -> None:
        OrderItem.query.filter(OrderItem.order_id == order_id).delete()

    @staticmethod
    def __delete_order(order_id: uuid.UUID) -> None:
        Order.query.filter(Order.id == order_id).delete()

    @staticmethod
    def __delete_roles(event_id: uuid.UUID) -> None:
        Role.query.filter(Role.event_id == event_id).delete()

    @staticmethod
    def __delete_event(event_id: uuid.UUID) -> None:
        Event.query.filter(Event.id == event_id).delete()

    @staticmethod
    def __delete_sizes(user_id: uuid.UUID) -> None:
        return Size.query.filter(Size.user_id == user_id).delete()

    @staticmethod
    def __delete_measurements(user_id: uuid.UUID) -> None:
        return Measurement.query.filter(Measurement.user_id == user_id).delete()

    @staticmethod
    def __delete_addresses(user_id: uuid.UUID) -> None:
        return Address.query.filter(Address.user_id == user_id).delete()

    @staticmethod
    def __num_attendees_with_look(look_id: uuid.UUID) -> int:
        return Attendee.query.filter(Attendee.look_id == look_id).count()

    @staticmethod
    def __delete_user(user_id: uuid.UUID) -> None:
        User.query.filter(User.id == user_id).delete()
