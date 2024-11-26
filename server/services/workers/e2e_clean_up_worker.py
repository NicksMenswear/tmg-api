import uuid
from logging import Logger
from typing import List

from sqlalchemy import func, select, delete, or_

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
    UserActivityLog,
)
from server.services import ServiceError
from server.services.integrations.shopify_service import AbstractShopifyService, ShopifyService

NUMBER_OF_USERS_TO_PROCESS = 30

SYSTEM_E2E_EMAILS_TO_KEEP = {
    "e2e+01@mail.dev.tmgcorp.net",
    "e2e+02@mail.dev.tmgcorp.net",
    "e2e+03@mail.dev.tmgcorp.net",
    "e2e+04@mail.dev.tmgcorp.net",
    "e2e+05@mail.dev.tmgcorp.net",
    "e2e+06@mail.dev.tmgcorp.net",
    "e2e+07@mail.dev.tmgcorp.net",
    "e2e+08@mail.dev.tmgcorp.net",
    "e2e+09@mail.dev.tmgcorp.net",
    "e2e+10@mail.dev.tmgcorp.net",
}

CUSTOMER_EMAIL_MATCHING_PATTERN = "e2e+*@mail.dev.tmgcorp.net"


class E2ECleanUpWorker:
    def __init__(self, shopify_service: AbstractShopifyService, logger: Logger):
        self.shopify_service = shopify_service
        self.logger = logger

    def get_customers(self, num_customers=250):
        num_customers = min(num_customers, 250)

        customers = self.shopify_service.get_customers_by_email_pattern(CUSTOMER_EMAIL_MATCHING_PATTERN, num_customers)
        customers.reverse()  # so system users are processed last

        result = []

        for customer in customers:
            result.append({"id": customer.gid, "email": customer.email})

        return result

    def cleanup(self, customer_gid: str, email: str) -> None:
        is_system_user = email in SYSTEM_E2E_EMAILS_TO_KEEP

        self.logger.info(f"Processing customer: {email}")

        try:
            user = self.__get_user_by_email(email)

            if not user:
                self.logger.error(f"User not found in db by email: {email}")

                self.__delete_shopify_customer(customer_gid)

                return

            attendees = self.__get_attendees(user.id)

            for attendee in attendees:
                discounts = self.__get_discounts(attendee.id)

                for discount in discounts:
                    discount_code = discount.shopify_discount_code

                    self.logger.info(f"Deleting discount: {discount_code}")

                    if discount.shopify_discount_code_id and discount_code:
                        self.__delete_shopify_discount(discount.shopify_discount_code_id)

                    self.__delete_discount(discount.id)
                self.__delete_attendee(attendee.id)

            events = self.__get_events(user.id)

            for event in events:
                num_active_attendees = self.__num_active_attendees_in_event(event.id)

                if num_active_attendees > 0:
                    self.logger.info(f"Event has attendees, skipping deletion: {event.id}")
                    continue

                num_inactive_or_without_user_attendees = self.__num_inactive_or_without_user_attendees_in_event(
                    event.id
                )

                if num_inactive_or_without_user_attendees == 0:
                    self.logger.info(f"Deleting event: {event.id}")

                    self.__delete_roles(event.id)

                    orders = self.__get_orders_for_event(event.id)

                    for order in orders:
                        self.logger.info(f"Deleting order: {order.id}")
                        self.__delete_order_items_for_order(order.id)
                        self.__delete_order(order.id)

                    self.__delete_event(event.id)
                else:
                    attendees = self.__get_inactive_attendees_for_event(event.id)

                    for attendee in attendees:
                        discounts = self.__get_discounts(attendee.id)

                        for discount in discounts:
                            discount_code = discount.shopify_discount_code

                            self.logger.info(f"Deleting discount: {discount_code}")

                            if discount.shopify_discount_code_id and discount_code:
                                self.__delete_shopify_discount(discount.shopify_discount_code_id)

                            self.__delete_discount(discount.id)

                        self.logger.info(f"Deleting attendee: {attendee.id}")
                        self.__delete_attendee(attendee.id)
                        try:
                            if attendee.user_id:
                                self.__delete_user(attendee.user_id)
                        except Exception as e:
                            self.logger.error(f"Failed to delete user: {attendee.user_id}")

                db.session.commit()

            self.__delete_sizes(user.id)
            self.__delete_measurements(user.id)
            self.__delete_addresses(user.id)

            looks = self.__get_user_looks(user.id)

            for look in looks:
                product_specs = look.product_specs

                if product_specs and product_specs.get("bundle", {}).get("product_id"):
                    shopify_bundle_product_id = product_specs["bundle"]["product_id"]

                    self.logger.info(f"Deleting bundle product: {shopify_bundle_product_id}")
                    self.__delete_shopify_product(shopify_bundle_product_id)

                    for item in product_specs.get("items", []):
                        if not item.get("variant_sku", "").startswith("bundle-"):
                            continue

                        self.logger.info(f"Deleting product: {item.get('product_id')}")
                        self.__delete_shopify_product(item.get("product_id"))

                attendees_with_look = self.__get_attendees_with_look(look.id)
                if not attendees_with_look:
                    self.logger.info(f"Deleting look: {look.id}/{look.name}")
                    self.__delete_look(look.id)

                db.session.commit()

            if is_system_user:
                db.session.commit()
                return

            self.logger.info(f"Deleting customer: {email}")

            self.__delete_shopify_customer(customer_gid)
            self.__delete_user_activity_logs(user.id)
            self.__delete_user(user.id)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.logger.exception(f"Failed to process customer: {email}")

    def bulk_cleanup(self) -> None:
        customers = self.get_customers(NUMBER_OF_USERS_TO_PROCESS)

        for customer in customers:
            self.cleanup(customer.get("id"), customer.get("email"))

    def __delete_shopify_customer(self, customer_gid: str) -> None:
        try:
            self.shopify_service.delete_customer(customer_gid)
        except ServiceError:
            self.logger.error(f"Failed to delete customer from shopify: {customer_gid}")

    def __delete_shopify_product(self, product_id: int) -> None:
        try:
            self.shopify_service.delete_product(ShopifyService.product_gid(product_id))
        except ServiceError:
            self.logger.exception(f"Failed to delete product from shopify: {product_id}")

    def __delete_shopify_discount(self, discount_id: int) -> None:
        try:
            self.shopify_service.delete_discount(f"gid://shopify/DiscountCodeNode/{discount_id}")
        except ServiceError:
            self.logger.error(f"Failed to delete discount from shopify: {discount_id}")

    @staticmethod
    def __num_active_attendees_in_event(event_id: uuid.UUID) -> int:
        return db.session.execute(select(func.count(Attendee.id)).where(Attendee.event_id == event_id, Attendee.is_active, Attendee.user_id.isnot(None))).scalar()  # type: ignore

    @staticmethod
    def __num_inactive_or_without_user_attendees_in_event(event_id: uuid.UUID) -> int:
        return db.session.execute(
            select(func.count(Attendee.id)).where(
                Attendee.event_id == event_id, or_(Attendee.is_active.is_(False), Attendee.user_id.is_(None))
            )
        ).scalar()  # type: ignore

    @staticmethod
    def __get_user_by_email(email: str) -> User:
        return db.session.execute(select(User).where(func.lower(User.email) == email.lower())).scalars().first()  # type: ignore

    @staticmethod
    def __get_events(user_id: uuid.UUID) -> List[Attendee]:
        return db.session.execute(select(Event).where(Event.user_id == user_id)).scalars().all()  # type: ignore

    @staticmethod
    def __get_attendees(user_id: uuid.UUID) -> List[Attendee]:
        return db.session.execute(select(Attendee).where(Attendee.user_id == user_id)).scalars().all()  # type: ignore

    @staticmethod
    def __get_inactive_attendees_for_event(event_id: uuid.UUID) -> List[Attendee]:
        return db.session.execute(select(Attendee).where(Attendee.event_id == event_id, or_(Attendee.is_active.is_(False), Attendee.user_id.is_(None)))).scalars().all()  # type: ignore

    @staticmethod
    def __get_attendees_with_look(look_id: uuid.UUID) -> List[Attendee]:
        return db.session.execute(select(Attendee).where(Attendee.look_id == look_id)).scalars().all()  # type: ignore

    @staticmethod
    def __delete_discount(discount_id: uuid.UUID) -> None:
        db.session.execute(delete(Discount).where(Discount.id == discount_id))  # type: ignore

    @staticmethod
    def __delete_look(look_id: uuid.UUID) -> None:
        db.session.execute(delete(Look).where(Look.id == look_id))  # type: ignore

    @staticmethod
    def __delete_attendee(attendee_id: uuid.UUID) -> None:
        db.session.execute(delete(Attendee).where(Attendee.id == attendee_id))  # type: ignore

    @staticmethod
    def __get_discounts(attendee_id: uuid.UUID) -> List[Discount]:
        return db.session.execute(select(Discount).where(Discount.attendee_id == attendee_id)).scalars().all()  # type: ignore

    @staticmethod
    def __get_user_looks(user_id: uuid.UUID) -> List[Look]:
        return db.session.execute(select(Look).where(Look.user_id == user_id)).scalars().all()  # type: ignore

    @staticmethod
    def __get_orders_for_event(event_id: uuid.UUID) -> List[Order]:
        return db.session.execute(select(Order).where(Order.event_id == event_id)).scalars().all()  # type: ignore

    @staticmethod
    def __delete_order_items_for_order(order_id: uuid.UUID) -> None:
        db.session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))  # type: ignore

    @staticmethod
    def __delete_order(order_id: uuid.UUID) -> None:
        db.session.execute(delete(Order).where(Order.id == order_id))  # type: ignore

    @staticmethod
    def __delete_roles(event_id: uuid.UUID) -> None:
        db.session.execute(delete(Role).where(Role.event_id == event_id))  # type: ignore

    @staticmethod
    def __delete_event(event_id: uuid.UUID) -> None:
        db.session.execute(delete(Event).where(Event.id == event_id))  # type: ignore

    @staticmethod
    def __delete_sizes(user_id: uuid.UUID) -> None:
        db.session.execute(delete(Size).where(Size.user_id == user_id))  # type: ignore

    @staticmethod
    def __delete_measurements(user_id: uuid.UUID) -> None:
        db.session.execute(delete(Measurement).where(Measurement.user_id == user_id))  # type: ignore

    @staticmethod
    def __delete_addresses(user_id: uuid.UUID) -> None:
        db.session.execute(delete(Address).where(Address.user_id == user_id))  # type: ignore

    @staticmethod
    def __num_attendees_with_look(look_id: uuid.UUID) -> int:
        return db.session.execute(select(func.count(Attendee.id)).where(Attendee.look_id == look_id)).scalar()  # type: ignore

    @staticmethod
    def __delete_user(user_id: uuid.UUID) -> None:
        db.session.execute(delete(User).where(User.id == user_id))  # type: ignore

    @staticmethod
    def __delete_user_activity_logs(user_id: uuid.UUID) -> None:
        activity_logs = db.session.execute(select(UserActivityLog).where(UserActivityLog.user_id == user_id)).scalars().all()  # type: ignore

        if not activity_logs:
            return

        for activity_log in activity_logs:
            db.session.execute(delete(UserActivityLog).where(UserActivityLog.id == activity_log.id))  # type: ignore

        db.session.execute(delete(UserActivityLog).where(User.id == user_id))  # type: ignore
