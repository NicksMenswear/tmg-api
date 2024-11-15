import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from server.database.models import SourceType, OrderType
from server.models.order_model import AddressModel, CreateOrderModel, CreateOrderItemModel
from server.models.product_model import CreateProductModel, ProductModel
from server.services import NotFoundError, ServiceError
from server.services.attendee_service import AttendeeService
from server.services.discount_service import (
    DISCOUNT_GIFT_FOR_ATTENDEE,
    DiscountService,
    GIFT_DISCOUNT_CODE_PREFIX,
    TMG_MIN_SUIT_PRICE,
)
from server.services.integrations.email_service import AbstractEmailService
from server.services.event_service import EventService
from server.services.integrations.activecampaign_service import AbstractActiveCampaignService
from server.services.integrations.shiphero_service import AbstractShipHeroService
from server.services.integrations.shopify_service import AbstractShopifyService, DiscountAmountType, ShopifyService
from server.services.integrations.sms_service import AbstractSmsService
from server.services.look_service import LookService
from server.services.measurement_service import MeasurementService
from server.services.order_service import (
    ORDER_STATUS_PENDING_MEASUREMENTS,
    ORDER_STATUS_PENDING_MISSING_SKU,
    ORDER_STATUS_READY,
    OrderService,
)
from server.services.product_service import ProductService
from server.services.size_service import SizeService
from server.services.sku_builder_service import SkuBuilder, ProductType
from server.services.user_service import UserService

logger = logging.getLogger(__name__)

BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX = "bundle-"


class ShopifyWebhookOrderHandler:
    def __init__(
        self,
        shopify_service: AbstractShopifyService,
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
        shiphero_service: AbstractShipHeroService,
        activecampaign_service: AbstractActiveCampaignService,
        email_service: AbstractEmailService,
        sms_service: AbstractSmsService,
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
        self.shiphero_service = shiphero_service
        self.activecampaign_service = activecampaign_service
        self.email_service = email_service
        self.sms_service = sms_service

    def order_paid(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for customer update: {webhook_id}")

        items = payload.get("line_items")

        if not items or len(items) == 0:
            return self.__error(f"Received paid order without items")

        return self.__process_paid_order(webhook_id, payload)

    @staticmethod
    def __error(message):
        logger.error(message)
        return {"errors": message}

    def __process_gift_discount(self, discount_line_item: Dict[str, Any], customer_email: str) -> None:
        shopify_product_id = discount_line_item.get("product_id")
        shopify_variant_id = discount_line_item.get("variant_id")

        logger.info(f"Handling discount for variant_id '{shopify_product_id}/{shopify_variant_id}'")

        try:
            self.shopify_service.archive_product(ShopifyService.product_gid(shopify_product_id))
        except Exception as e:
            logger.warning(
                f"Error archiving product with id '{shopify_product_id}/{shopify_variant_id}': {e}"
            )  # log but proceed

        discounts = self.discount_service.get_gift_discount_intents_for_product_variant(shopify_variant_id)

        if not discounts:
            logger.error(f"No discounts found for product_id: {shopify_product_id}")
            return

        discounts_codes = []

        event_id = discounts[0].event_id
        event = self.event_service.get_event_by_id(event_id)
        owner_user = self.user_service.get_user_by_id(event.user_id)

        for discount in discounts:
            attendee_user = self.user_service.get_user_for_attendee(discount.attendee_id)
            attendee = self.attendee_service.get_attendee_by_id(discount.attendee_id)

            if not attendee.look_id:
                logger.error(f"No look associated for attendee '{attendee.id}' can't create discount code")
                return

            look = self.look_service.get_look_by_id(attendee.look_id)

            if (
                not look
                or not look.product_specs
                or not look.product_specs.get("bundle", {}).get("variant_id")
                or not look.product_specs.get("items")
            ):
                logger.error(f"No shopify variants founds for look {look.id}. Can't create discount code")
                return

            code = f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount.amount)}-OFF-{random.randint(100000, 9999999)}"

            discount_response = self.shopify_service.create_discount_code(
                code,
                code,
                attendee_user.shopify_id,
                DiscountAmountType.FIXED_AMOUNT,
                discount.amount,
                TMG_MIN_SUIT_PRICE,
            )

            self.discount_service.add_code_to_discount(
                discount.id,
                discount_response.get("shopify_discount_id"),
                discount_response.get("shopify_discount_code"),
            )

            discounts_codes.append(discount_response.get("shopify_discount_code"))

            try:
                self.email_service.send_gift_discount_code_email(
                    event, owner_user, attendee_user, discount_response.get("shopify_discount_code")
                )
            except Exception as e:
                logger.exception(e)

        if discounts_codes:
            self.__track_giftcode_purchase(customer_email)

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

        self.__process_used_discount_code(payload)
        self.__track_swatch_purchase(user, payload)
        self.__sms_order_received(user, shopify_order_number)

        shopify_order_id = payload.get("id")
        created_at = datetime.fromisoformat(payload.get("created_at"))
        shipping_address = payload.get("shipping_address")
        if shipping_address:
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

        num_valid_products = 0
        has_products_that_requires_measurements = False
        track_suit_parts = {}
        order_number = self.order_service.generate_order_number()
        ship_by_date = None  # self.__calculate_ship_by_date(event_id) if event_id else None # decided to not use this - manual process only for now

        num_processable_items = len(items)
        order_id = None

        line_item_skus = set()

        for line_item in items:
            shopify_sku = line_item.get("sku")
            line_item_skus.add(shopify_sku)

            if not shopify_sku:
                logger.error(f'No SKU found for line item: {line_item.get("name")} in order {shopify_order_number}')

            if shopify_sku and shopify_sku.startswith(BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX):
                # Skip bundle products which are just markers for the bundle
                num_processable_items -= 1
                continue

            if shopify_sku and (
                shopify_sku.startswith(DISCOUNT_GIFT_FOR_ATTENDEE)
                or shopify_sku.startswith("DISCOUNT-")  # DISCOUNT- sku is for legacy discount codes
            ):
                self.__process_gift_discount(line_item, shopify_customer_email)
                num_processable_items -= 1

            if not order_id:
                shipping_method = None

                if payload.get("shipping_lines") and len(payload.get("shipping_lines")) > 0:
                    shipping_method = payload.get("shipping_lines")[0].get("title")
                else:
                    shipping_method = "Shipping not required"

                create_order = CreateOrderModel(
                    user_id=user.id,
                    order_number=order_number,
                    shopify_order_id=str(shopify_order_id),
                    shopify_order_number=str(shopify_order_number),
                    order_origin=SourceType.TMG.value,
                    order_date=created_at,
                    order_type=[OrderType.NEW_ORDER.value],
                    shipping_address=shipping_address,
                    shipping_method=shipping_method,
                    event_id=event_id,
                    ship_by_date=ship_by_date,
                    meta={
                        "webhook_id": str(webhook_id),
                        "sizes_id": str(size_model.id) if size_model else None,
                        "measurements_id": str(measurement_model.id) if measurement_model else None,
                    },
                )

                order = self.order_service.create_order(create_order)
                order_id = order.id

            shiphero_sku = None
            product = None
            product_type = self.sku_builder.get_product_type_by_sku(shopify_sku)

            try:
                shiphero_sku = self.sku_builder.build(shopify_sku, size_model, measurement_model)

                if product_type in {ProductType.JACKET, ProductType.VEST, ProductType.PANTS}:
                    shopify_suit_sku_suffix = f"{shopify_sku[-5:]}"
                    track_suit_parts[shopify_suit_sku_suffix] = track_suit_parts.get(shopify_suit_sku_suffix, {})
                    track_suit_parts[shopify_suit_sku_suffix][product_type] = shopify_sku

                    if ProductType.SUIT not in track_suit_parts[shopify_suit_sku_suffix]:
                        track_suit_parts[shopify_suit_sku_suffix][ProductType.SUIT] = f"0{shopify_sku[1:]}"

                if not shiphero_sku:
                    if product_type is not ProductType.UNKNOWN and size_model and measurement_model:
                        logger.error(
                            f"ShipHero SKU not generated for '{shopify_sku}' in order '{shopify_order_number}'"
                        )

                    if self.sku_builder.does_product_requires_measurements(shopify_sku):
                        has_products_that_requires_measurements = True
            except ServiceError as e:
                logger.error(f"Error building ShipHero SKU for '{shopify_sku}': {e}")

            if shiphero_sku and product_type is not ProductType.UNKNOWN:
                product = self.__get_product_by_shiphero_sku(shiphero_sku)

                if product:
                    num_valid_products += 1

            create_order_item = CreateOrderItemModel(
                order_id=order_id,
                product_id=product.id if product else None,
                shopify_sku=shopify_sku,
                purchased_price=line_item.get("price"),
                quantity=line_item.get("quantity"),
            )

            self.order_service.create_order_item(create_order_item)

        if track_suit_parts:
            for shopify_suit_sku_suffix, suit_parts in track_suit_parts.items():
                if len(suit_parts) != 4:
                    # Looks like order is not a full suit split, skipping
                    continue

                shopify_suit_sku = suit_parts[ProductType.SUIT]
                suit_variant = self.shopify_service.get_variant_by_sku(shopify_suit_sku)
                shiphero_suit_sku = self.sku_builder.build(shopify_suit_sku, size_model, measurement_model)
                suit_product = None

                if shiphero_suit_sku:
                    suit_product = self.__get_product_by_shiphero_sku(shiphero_suit_sku)
                    self.__track_suit_purchase(user.email)

                create_suit_order_item = CreateOrderItemModel(
                    order_id=order_id,
                    product_id=suit_product.id if suit_product else None,
                    shopify_sku=shopify_suit_sku,
                    purchased_price=suit_variant.variant_price,
                    quantity=1,
                )

                self.order_service.create_order_item(create_suit_order_item)

        if num_valid_products < num_processable_items:
            if has_products_that_requires_measurements and not (size_model or measurement_model):
                order_status = ORDER_STATUS_PENDING_MEASUREMENTS
            else:
                order_status = ORDER_STATUS_PENDING_MISSING_SKU
        else:
            order_status = ORDER_STATUS_READY

        if event_id and user.id:
            try:
                look = self.look_service.get_user_look_for_event(user.id, event_id)
                items = look.product_specs.get("items", {})

                num_items_in_look = len(items)
                num_matched_items_in_order = 0

                for item in items:
                    if item.get("variant_sku", item.get("sku", "")) in line_item_skus:
                        num_matched_items_in_order += 1

                if num_items_in_look <= num_matched_items_in_order:
                    self.attendee_service.update_attendee_pay_status(event_id, user.id)
            except NotFoundError:
                logger.warning(
                    f"Error updating attendee pay status for event_id '{event_id}' and user_id '{user.id}'. Attendee not found."
                )

        order_model = self.order_service.update_order_status(order_id, order_status, size_model, measurement_model)
        order_model.order_items = self.order_service.get_order_items_by_order_id(order_id)
        order_model.products = self.product_service.get_products_for_order(order_id)

        return order_model.to_response()

    @staticmethod
    def __get_event_id_from_note_attributes(payload: Dict[str, Any]) -> Optional[uuid.UUID]:
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

    def __get_product_by_shiphero_sku(self, shiphero_sku: str) -> Optional[ProductModel]:
        product = None

        try:
            product = self.product_service.get_product_by_sku(shiphero_sku)
        except NotFoundError:
            logger.debug(f"No product found for ShipHero SKU '{shiphero_sku}' in our db. Pulling from ShipHero API")

        if product:
            return product

        try:
            shiphero_product = self.shiphero_service.get_product_by_sku(shiphero_sku)
        except Exception as e:
            logger.error(f"Error fetching product from ShipHero for SKU '{shiphero_sku}': {e}")
            return None

        try:
            product = self.product_service.create_product(
                CreateProductModel(**shiphero_product.model_dump(exclude={"id"}))
            )
        except ServiceError as e:
            logger.error(f"Error creating product from ShipHero for SKU '{shiphero_sku}': {e}")
            return None

        return ProductModel.model_validate(product)

    def __track_swatch_purchase(self, user, payload):
        items = payload.get("line_items", [])
        if any(item.get("sku", "").upper().startswith("S") for item in items):
            self.activecampaign_service.sync_contact(
                email=user.email,
                fields={"ORDERED_SWATCHES": "Yes"},
                events=["Ordered Swatches"],
            )

    def __track_giftcode_purchase(self, user_email):
        self.activecampaign_service.sync_contact(
            email=user_email,
            fields={"PAID_FOR_ATTENDEES": "Yes"},
            events=["Paid for Attendees"],
        )

    def __track_suit_purchase(self, user_email):
        self.activecampaign_service.sync_contact(
            email=user_email,
            fields={"PAID_FOR_A_SUIT": "Yes"},
            events=["Paid for a Suit"],
        )

    def __sms_order_received(self, user, order_number):
        if not user.phone_number:
            return
        if not user.sms_consent:
            return
        self.sms_service.send_order_confirmation(user.phone_number, order_number)
