import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from server.database.models import SourceType, OrderType
from server.models.order_model import AddressModel, CreateProductModel, CreateOrderModel
from server.services import NotFoundError, ServiceError
from server.services.attendee_service import AttendeeService
from server.services.discount_service import DISCOUNT_VIRTUAL_PRODUCT_PREFIX, DiscountService, GIFT_DISCOUNT_CODE_PREFIX
from server.services.event_service import EventService
from server.services.look_service import LookService
from server.services.measurement_service import MeasurementService
from server.services.order_service import (
    ORDER_STATUS_PENDING_MEASUREMENTS,
    ORDER_STATUS_PENDING_MISSING_SKU,
    ORDER_STATUS_READY,
    OrderService,
)
from server.services.product_service import ProductService
from server.services.shopify_service import ShopifyService
from server.services.size_service import SizeService
from server.services.sku_builder_service import SkuBuilder, ProductType
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ShopifyWebhookOrderHandler:
    def __init__(
        self,
        shopify_service: ShopifyService,
        discount_service: DiscountService,
        user_service: UserService,
        attendee_service: AttendeeService,
        look_service: LookService,
        size_service: SizeService,
        measurement_service: MeasurementService,
        order_service: OrderService,
        product_service: ProductService,
        sku_builder: SkuBuilder,
        event_service: EventService,
    ):
        self.shopify_service = shopify_service
        self.discount_service = discount_service
        self.user_service = user_service
        self.attendee_service = attendee_service
        self.look_service = look_service
        self.size_service = size_service
        self.measurement_service = measurement_service
        self.order_service = order_service
        self.product_service = product_service
        self.sku_builder = sku_builder
        self.event_service = event_service

    def order_paid(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for customer update: {webhook_id}")

        items = payload.get("line_items")

        if not items or len(items) == 0:
            return self.__error(f"Received paid order without items")

        if len(items) == 1 and items[0].get("sku") and items[0].get("sku").startswith(DISCOUNT_VIRTUAL_PRODUCT_PREFIX):
            sku = items[0].get("sku")
            logger.debug(f"Found paid discount order with sku '{sku}'")
            return self.__process_gift_discount(payload)

        return self.__process_paid_order(webhook_id, payload)

    def __error(self, message):
        logger.error(message)
        return {"errors": message}

    def __process_gift_discount(self, payload):
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
            logger.warning(
                f"Error archiving product with id '{shopify_product_id}/{shopify_variant_id}': {e}"
            )  # log but proceed

        discounts = self.discount_service.get_gift_discount_intents_for_product_variant(shopify_variant_id)

        if not discounts:
            return self.__error(f"No discounts found for product_id: {shopify_product_id}")

        discounts_codes = []

        for discount in discounts:
            attendee_user = self.user_service.get_user_for_attendee(discount.attendee_id)
            attendee = self.attendee_service.get_attendee_by_id(discount.attendee_id)

            if not attendee.look_id:
                return self.__error(f"No look associated for attendee '{attendee.id}' can't create discount code")

            look = self.look_service.get_look_by_id(attendee.look_id)

            if (
                not look
                or not look.product_specs
                or not look.product_specs.get("bundle", {}).get("variant_id")
                or not look.product_specs.get("items")
            ):
                return self.__error(f"No shopify variants founds for look {look.id}. Can't create discount code")

            code = f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount.amount)}-OFF-{random.randint(100000, 9999999)}"

            bundle_variant_id = look.product_specs.get("bundle", {}).get("variant_id")
            discounted_variant_ids = [bundle_variant_id]

            discount_response = self.shopify_service.create_discount_code(
                code, code, attendee_user.shopify_id, discount.amount, discounted_variant_ids
            )

            self.discount_service.add_code_to_discount(
                discount.id,
                discount_response.get("shopify_discount_id"),
                discount_response.get("shopify_discount_code"),
            )

            discounts_codes.append(discount_response.get("shopify_discount_code"))

        return {"discount_codes": discounts_codes}

    def __process_used_discount_code(self, payload):
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

    def __process_paid_order(self, webhook_id: uuid.UUID, payload: Dict[str, Any]):
        shopify_order_number = payload.get("order_number")
        items = payload.get("line_items")

        shopify_customer_email = payload.get("customer").get("email")

        try:
            user = self.user_service.get_user_by_email(shopify_customer_email)
        except NotFoundError:
            return self.__error(
                f"No user found for email '{shopify_customer_email}'. Processing order via webhook: {payload}"
            )

        tmg_issued_discount_codes = self.__process_used_discount_code(payload)

        shopify_order_id = payload.get("id")
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

        event_id = self.__get_event_id_from_note_attributes(payload)
        size_model = self.size_service.get_latest_size_for_user(user.id)
        measurement_model = self.measurement_service.get_latest_measurement_for_user(user.id) if size_model else None

        num_shiphero_skus = 0
        has_products_that_requires_measurements = False

        track_suit_parts = {}

        products = []

        for line_item in items:
            shopify_sku = line_item.get("sku")

            if not shopify_sku:
                logger.error(f'No SKU found for line item: {line_item.get("name")} in order {shopify_order_number}')
                continue

            shiphero_sku = None

            try:
                shiphero_sku = self.sku_builder.build(shopify_sku, size_model, measurement_model)
                product_type = self.sku_builder.get_product_type_by_sku(shopify_sku)

                if product_type in {ProductType.JACKET, ProductType.VEST, ProductType.PANTS}:
                    shopify_suit_sku = f"0{shopify_sku[1:]}"
                    track_suit_parts[shopify_suit_sku] = track_suit_parts.get(shopify_suit_sku, {})
                    track_suit_parts[shopify_suit_sku][product_type] = shopify_sku

                if shiphero_sku:
                    num_shiphero_skus += 1
                elif size_model and measurement_model:
                    logger.error(f"ShipHero SKU not generated for '{shopify_sku}' in order '{shopify_order_number}'")

                if not shiphero_sku and self.sku_builder.does_product_requires_measurements(shopify_sku):
                    has_products_that_requires_measurements = True
            except ServiceError as e:
                logger.error(f"Error building ShipHero SKU for '{shopify_sku}': {e}")

            create_product = CreateProductModel(
                name=line_item.get("name"),
                sku=shiphero_sku,
                shopify_sku=shopify_sku,
                price=line_item.get("price"),
                quantity=1,
            )

            products.append(create_product)

        if track_suit_parts:
            for shopify_suit_sku, suit_parts in track_suit_parts.items():
                if len(suit_parts) != 3:
                    # Looks like order is not a full suit split, skipping
                    continue

                suit_variant = self.shopify_service.get_variant_by_sku(shopify_suit_sku)
                shiphero_suit_sku = self.sku_builder.build(shopify_suit_sku, size_model, measurement_model)

                create_product = CreateProductModel(
                    name=suit_variant.product_title,
                    sku=shiphero_suit_sku,
                    shopify_sku=shopify_suit_sku,
                    price=suit_variant.variant_price,
                    quantity=1,
                )

                products.append(create_product)

        order_number = self.order_service.generate_order_number()

        if num_shiphero_skus < len(items):
            if has_products_that_requires_measurements and not (size_model or measurement_model):
                order_status = ORDER_STATUS_PENDING_MEASUREMENTS
            else:
                order_status = ORDER_STATUS_PENDING_MISSING_SKU
        else:
            order_status = ORDER_STATUS_READY

        # ship_by_date = self.__calculate_ship_by_date(event_id) if event_id else None # decided to not use this - manual process only for now
        ship_by_date = None

        create_order = CreateOrderModel(
            user_id=user.id,
            order_number=order_number,
            shopify_order_id=str(shopify_order_id),
            shopify_order_number=str(shopify_order_number),
            order_origin=SourceType.TMG.value,
            order_date=created_at,
            order_type=[OrderType.NEW_ORDER.value],
            shipping_address=shipping_address,
            products=products,
            event_id=event_id,
            meta={"webhook_id": str(webhook_id)},
            status=order_status,
            ship_by_date=ship_by_date,
        )

        try:
            order_model = self.order_service.create_order(create_order)
            order_model.discount_codes = tmg_issued_discount_codes

            if event_id and user.id:
                try:
                    self.attendee_service.update_attendee_pay_status(event_id, user.id)
                except NotFoundError:
                    logger.error(
                        f"Error updating attendee pay status for event_id '{event_id}' and user_id '{user.id}'. Attendee not found."
                    )

            return order_model.to_response()
        except Exception as e:
            return self.__error(f"Error creating order: {str(e)}")

    def __get_event_id_from_note_attributes(self, payload: Dict[str, Any]) -> Optional[uuid.UUID]:
        note_attributes = payload.get("note_attributes")

        if not note_attributes:
            return None

        for note_attribute in note_attributes:
            if note_attribute.get("name") != "__event_id":
                continue

            try:
                return uuid.UUID(note_attribute.get("value"))
            except ValueError:
                logger.error(f"Invalid event_id in note attributes: {note_attribute.get('value')}")
                return None

    def __calculate_ship_by_date(self, event_id: uuid.UUID, num_week_before_event: int = 6) -> Optional[datetime]:
        try:
            event = self.event_service.get_event_by_id(event_id)
        except NotFoundError:
            return None

        date_n_weeks_ago = event.event_at - timedelta(weeks=num_week_before_event)
        monday_of_week = date_n_weeks_ago - timedelta(days=date_n_weeks_ago.weekday())  # Find the Monday of that week

        if monday_of_week < datetime.now():
            return None

        return monday_of_week
