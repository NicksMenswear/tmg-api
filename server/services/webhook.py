import logging
import random
import uuid
from datetime import datetime

from server.database.models import SourceType, OrderType, StoreLocation
from server.models.order_model import CreateOrderModel, AddressModel, CreateProductModel
from server.models.user_model import UserModel, CreateUserModel, UpdateUserModel
from server.services import ServiceError, NotFoundError
from server.services.attendee import AttendeeService
from server.services.discount import (
    DiscountService,
    DISCOUNT_VIRTUAL_PRODUCT_PREFIX,
    GIFT_DISCOUNT_CODE_PREFIX,
)
from server.services.look import LookService
from server.services.order import OrderService
from server.services.shopify import ShopifyService
from server.services.user import UserService

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class WebhookService:
    def __init__(
        self,
        user_service: UserService,
        attendee_service: AttendeeService,
        discount_service: DiscountService,
        look_service: LookService,
        shopify_service: ShopifyService,
        order_service: OrderService,
    ):
        self.user_service = user_service
        self.attendee_service = attendee_service
        self.discount_service = discount_service
        self.look_service = look_service
        self.shopify_service = shopify_service
        self.order_service = order_service

    def __error(self, message):
        return {"errors": message}

    def handle_orders_paid(self, payload):
        items = payload.get("line_items")

        if not items or len(items) == 0:
            logger.debug(f"Received paid order without items")
            return self.__error("No items in order")

        if len(items) == 1 and items[0].get("sku") and items[0].get("sku").startswith(DISCOUNT_VIRTUAL_PRODUCT_PREFIX):
            sku = items[0].get("sku")
            logger.debug(f"Found paid discount order with sku '{sku}'")
            return self.process_gift_discount(payload)

        return self.process_paid_order(payload)

    def handle_customer_update(self, payload):
        shopify_id = payload.get("id")
        email = payload.get("email")
        first_name = payload.get("first_name")
        last_name = payload.get("last_name")
        state = payload.get("state")
        phone = payload.get("phone")

        try:
            user = self.user_service.get_user_by_email(email)
        except NotFoundError:
            user = None

        if not user:
            updated_user = self.user_service.create_user(
                CreateUserModel(
                    shopify_id=str(shopify_id),
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    account_status=True if state == "enabled" else False,
                    phone_number=str(phone),
                )
            )

            return updated_user.to_response()
        elif (
            str(shopify_id) != user.shopify_id
            or email != user.email
            or first_name != user.first_name
            or last_name != user.last_name
            or str(phone) != user.phone_number
            or (state == "enabled" and not user.account_status)
        ):
            updated_user = self.user_service.update_user(
                user.id,
                UpdateUserModel(
                    first_name=first_name,
                    last_name=last_name,
                    account_status=True if state == "enabled" else False,
                    shopify_id=str(shopify_id),
                    phone_number=str(phone),
                ),
            )

            return updated_user.to_response()
        else:
            return user.to_response()

    def process_gift_discount(self, payload):
        product = payload.get("line_items")[0]
        customer = payload.get("customer")

        shopify_product_id = product.get("product_id")
        shopify_variant_id = product.get("variant_id")
        shopify_customer_id = customer.get("id")

        logger.info(
            f"Handling discount for variant_id '{shopify_product_id}/{shopify_variant_id}' and customer_id '{shopify_customer_id}'"
        )

        try:
            self.shopify_service.archive_product(shopify_product_id)
        except Exception as e:
            logger.error(
                f"Error archiving product with id '{shopify_product_id}/{shopify_variant_id}': {e}"
            )  # log but proceed

        discounts = self.discount_service.get_gift_discount_intents_for_product(shopify_variant_id)

        if not discounts:
            logger.error(f"No discounts found for product_id: {shopify_product_id}")
            return self.__error("No discounts found for product")

        discounts_codes = []

        for discount in discounts:
            attendee_user = self.user_service.get_user_for_attendee(discount.attendee_id)
            attendee = self.attendee_service.get_attendee_by_id(discount.attendee_id)

            if not attendee.look_id:
                logger.error(f"No look associated for attendee '{attendee.id}' can't create discount code")
                return self.__error(f"No look associated for attendee '{attendee.id}' can't create discount code")

            look = self.look_service.get_look_by_id(attendee.look_id)

            if not look or not look.product_specs or len(look.product_specs.get("variants", [])) == 0:
                logger.error(f"No shopify variants founds for look {look.id}. Can't create discount code")
                return self.__error(f"No shopify variants founds for look {look.id}. Can't create discount code")

            code = f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount.amount)}-OFF-{random.randint(100000, 9999999)}"

            discount_response = self.shopify_service.create_discount_code(
                code,
                code,
                attendee_user.shopify_id,
                discount.amount,
                look.product_specs.get("variants"),
            )

            self.discount_service.add_code_to_discount(
                discount.id,
                discount_response.get("shopify_discount_id"),
                discount_response.get("shopify_discount_code"),
            )

            discounts_codes.append(discount_response.get("shopify_discount_code"))

        return {"discount_codes": discounts_codes}

    def process_used_discount_code(self, payload):
        discount_codes = payload.get("discount_codes", [])

        if len(discount_codes) == 0:
            logger.debug(f"No discount codes found in payload")
            return []

        used_discount_codes = []

        for discount_code in discount_codes:
            shopify_discount_code = discount_code.get("code")

            discount = self.discount_service.mark_discount_by_shopify_code_as_paid(shopify_discount_code)

            if discount:
                used_discount_codes.append(shopify_discount_code)
                logger.info(f"Marked discount with code '{shopify_discount_code}' with id '{discount.id}' as paid")

        return used_discount_codes

    def process_paid_order(self, payload):
        shopify_customer_email = payload.get("customer").get("email")

        user = self.user_service.get_user_by_email(shopify_customer_email)

        if not user:
            logger.error(f"No user found for email '{shopify_customer_email}'. Processing order via webhook: {payload}")
            return self.__error(f"No user found for email '{shopify_customer_email}'")

        tmg_issued_discount_codes = self.process_used_discount_code(payload)

        order_number = payload.get("order_number")
        created_at = datetime.fromisoformat(payload.get("created_at"))
        shipping_address = payload.get("shipping_address")
        shipping_address = AddressModel(
            line1=shipping_address.get("address1"),
            line2=shipping_address.get("address2"),
            city=shipping_address.get("city"),
            state=shipping_address.get("province"),
            zip_code=shipping_address.get("zip"),
            country=shipping_address.get("country"),
        )

        create_products = []

        if payload.get("line_items"):
            for line_item in payload.get("line_items"):
                create_product = CreateProductModel(
                    name=line_item.get("name"),
                    sku=line_item.get("sku"),
                    price=line_item.get("price"),
                    quantity=line_item.get("quantity"),
                    meta={"webhook_line_item_id": line_item.get("id")},
                )

                create_products.append(create_product)

        create_order = CreateOrderModel(
            user_id=user.id,
            order_number=str(order_number),
            order_origin=SourceType.TMG.value,
            order_date=created_at,
            order_type=[OrderType.NEW_ORDER.value],
            shipping_address=shipping_address,
            store_location=StoreLocation.ONLINE.value,
            products=create_products,
            meta=payload,
        )

        try:
            order_model = self.order_service.create_order(create_order)
            order_model.discount_codes = tmg_issued_discount_codes

            return order_model.to_response()
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return self.__error(f"Error creating order: {str(e)}")
