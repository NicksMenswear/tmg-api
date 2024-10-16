import logging
import random
import uuid
from datetime import datetime, timezone
from operator import or_
from typing import List, Optional, Set, Dict
from uuid import UUID

from server.database.database_manager import db
from server.database.models import Discount, Attendee, DiscountType, Event, User, Look
from server.models.attendee_model import AttendeeModel
from server.models.discount_model import (
    DiscountModel,
    CreateDiscountIntent,
    DiscountGiftCodeModel,
    EventDiscountModel,
    DiscountLookModel,
    DiscountStatusModel,
    DiscountPayResponseModel,
)
from server.models.shopify_model import ShopifyProduct
from server.services import ServiceError, NotFoundError, BadRequestError
from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import AbstractShopifyService, DiscountAmountType, ShopifyService
from server.services.look_service import LookService
from server.services.user_service import UserService

DISCOUNT_VIRTUAL_PRODUCT_PREFIX = "DISCOUNT"
GIFT_DISCOUNT_CODE_PREFIX = "GIFT"
TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX = "TMG-GROUP-50-OFF"
TMG_GROUP_50_USD_AMOUNT = 50
TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX = "TMG-GROUP-25%-OFF"
TMG_GROUP_25_PERCENT_OFF = 0.25
TMG_MIN_SUIT_PRICE_FOR_25_PERCENT_OFF = 300
TMG_MIN_SUIT_PRICE: int = 260

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class DiscountService:
    def __init__(
        self,
        shopify_service: AbstractShopifyService,
        user_service: UserService,
        event_service: EventService,
        attendee_service: AttendeeService,
        look_service: LookService,
    ):
        self.shopify_service = shopify_service
        self.user_service = user_service
        self.event_service = event_service
        self.attendee_service = attendee_service
        self.look_service = look_service

    def get_discount_by_id(self, discount_id: uuid.UUID) -> Discount:
        discount = Discount.query.filter(Discount.id == discount_id).first()

        if not discount:
            raise NotFoundError("Discount not found.")

        return discount

    def get_discounts_by_attendee_id(self, attendee_id: uuid.UUID) -> List[DiscountModel]:
        return [
            DiscountModel.model_validate(discount)
            for discount in Discount.query.filter(Discount.attendee_id == attendee_id).all()
        ]

    def get_discount_by_shopify_code(self, shopify_code: str) -> Optional[DiscountModel]:
        discount = Discount.query.filter(Discount.shopify_discount_code == shopify_code).first()

        if not discount:
            return None

        return DiscountModel.model_validate(discount)

    def create_discount(
        self,
        event_id,
        attendee_id,
        amount,
        discount_type=DiscountType.GIFT,
        used=False,
        shopify_discount_code=None,
        shopify_discount_code_id=None,
        shopify_virtual_product_id=None,
        shopify_virtual_product_variant_id=None,
    ):
        discount = Discount(
            event_id=event_id,
            attendee_id=attendee_id,
            amount=amount,
            type=discount_type,
            used=used,
            shopify_discount_code=shopify_discount_code,
            shopify_discount_code_id=shopify_discount_code_id,
            shopify_virtual_product_id=shopify_virtual_product_id,
            shopify_virtual_product_variant_id=shopify_virtual_product_variant_id,
        )

        db.session.add(discount)
        db.session.commit()

        return discount

    def get_discounts_for_event(self, event_id: UUID) -> List[Discount]:
        event = self.event_service.get_event_by_id(event_id)

        if not event:
            raise NotFoundError("Event not found.")

        return Discount.query.filter(Discount.event_id == event_id).all()

    def get_owner_discounts_for_event(self, event_id: UUID) -> List[EventDiscountModel]:
        event = self.event_service.get_event_by_id(event_id)

        if not event:
            raise NotFoundError("Event not found.")

        users_attendees_looks = (
            db.session.query(Attendee, User, Look, Event)
            .outerjoin(User, User.id == Attendee.user_id)
            .outerjoin(Look, Attendee.look_id == Look.id)
            .join(Event, event_id == Event.id)
            .filter(Attendee.event_id == event_id, Attendee.is_active)
            .all()
        )

        if not users_attendees_looks:
            return []

        look_bundle_prices = self.__fetch_look_prices(users_attendees_looks)

        owner_discounts = {}

        num_attendees = 0

        for attendee, user, look, event in users_attendees_looks:
            look_model = None

            if look and look.product_specs:
                bundle_variant_id = look.product_specs.get("bundle", {}).get("variant_id")

                if bundle_variant_id:
                    look_price = look_bundle_prices.get(bundle_variant_id, 0.0)
                    look_model = DiscountLookModel(id=look.id, name=look.name, price=float(look_price))

            num_attendees += 1

            owner_discounts[attendee.id] = EventDiscountModel(
                event_id=event_id,
                amount=0.0,
                type=DiscountType.GIFT,
                attendee_id=attendee.id,
                user_id=user.id if user else None,
                is_owner=(user.id == event.user_id) if user else False,
                first_name=attendee.first_name or user.first_name,
                last_name=attendee.last_name or user.last_name,
                look=look_model,
                status=DiscountStatusModel(style=attendee.style, invite=attendee.invite, pay=attendee.pay),
            )

        attendee_ids = owner_discounts.keys()

        self.__enrich_owner_discounts_with_discount_intents_information(owner_discounts, attendee_ids, event_id)
        self.__enrich_owner_discounts_with_paid_discounts_information(owner_discounts, attendee_ids, event_id)

        if num_attendees >= 4:
            self.__enrich_owner_discounts_with_tmg_group_virtual_discount_code(owner_discounts, attendee_ids)

        self.__calculate_remaining_amount(owner_discounts)

        return self.__sort_owner_discounts(owner_discounts)

    def __sort_owner_discounts(self, owner_discounts: Dict[uuid.UUID, EventDiscountModel]) -> List[EventDiscountModel]:
        # Event owner
        # Attendees without gift codes with style/invite, sorted by Last Name, First Name
        # Attendees without gift codes without style/invite, sorted by Last Name, First Name
        # Attendees with gift codes sorted by Last Name, First Name
        return sorted(
            owner_discounts.values(),
            key=lambda discount: (
                not discount.is_owner,
                bool([c for c in discount.gift_codes if c.type == str(DiscountType.GIFT)]),
                not (discount.status.style and discount.status.invite),
                discount.last_name,
                discount.first_name,
            ),
        )

    def __calculate_remaining_amount(self, owner_discounts: Dict[uuid.UUID, EventDiscountModel]):
        for attendee_id in owner_discounts.keys():
            owner_discount = owner_discounts[attendee_id]

            if not owner_discount.look:
                owner_discount.remaining_amount = 0
                continue

            if owner_discount.status.pay:
                owner_discount.remaining_amount = 0
                continue

            owner_discount.remaining_amount = owner_discount.look.price

            if len(owner_discount.gift_codes) == 0:
                continue

            for gift_code in owner_discount.gift_codes:
                owner_discount.remaining_amount -= gift_code.amount

    def __fetch_look_prices(self, users_attendees_looks: List[tuple]) -> Dict[str, float]:
        look_bundle_prices: Dict[str, float] = dict()

        for _, _, look, _ in users_attendees_looks:
            if not look or not look.product_specs:
                continue

            bundle_variant_id = look.product_specs.get("bundle", {}).get("variant_id")
            look_bundle_prices[bundle_variant_id] = self.look_service.get_look_price(look)

        return look_bundle_prices

    def __enrich_owner_discounts_with_discount_intents_information(self, owner_discounts, attendee_ids, event_id):
        discount_intents = Discount.query.filter(
            Discount.event_id == event_id,
            Discount.type == DiscountType.GIFT,
            Discount.shopify_discount_code == None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for discount_intent in discount_intents:
            owner_discount = owner_discounts[discount_intent.attendee_id]
            owner_discount.attendee_id = discount_intent.attendee_id
            owner_discount.type = discount_intent.type
            owner_discount.amount = discount_intent.amount

    def __enrich_owner_discounts_with_paid_discounts_information(self, owner_discounts, attendee_ids, event_id):
        paid_discounts = Discount.query.filter(
            Discount.event_id == event_id,
            or_(Discount.type == DiscountType.GIFT, Discount.type == DiscountType.PARTY_OF_FOUR),
            Discount.shopify_discount_code != None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for paid_discount in paid_discounts:
            owner_discounts[paid_discount.attendee_id].gift_codes.append(
                DiscountGiftCodeModel(
                    code=paid_discount.shopify_discount_code,
                    amount=paid_discount.amount,
                    type=str(paid_discount.type),
                    used=paid_discount.used,
                )
            )

    def __enrich_owner_discounts_with_tmg_group_virtual_discount_code(self, owner_discounts, attendee_ids):
        for attendee_id in attendee_ids:
            owner_discount = owner_discounts[attendee_id]

            if not owner_discount.look:
                continue

            if owner_discount.status.pay:
                continue

            already_has_group_discount_paid = False

            if owner_discount.gift_codes:
                for gift_code in owner_discount.gift_codes:
                    if gift_code.type == str(DiscountType.PARTY_OF_FOUR):
                        already_has_group_discount_paid = True
                        break

            if already_has_group_discount_paid:
                continue

            look_price = owner_discount.look.price

            if look_price <= TMG_MIN_SUIT_PRICE_FOR_25_PERCENT_OFF:
                owner_discount.gift_codes.append(
                    DiscountGiftCodeModel(
                        code=TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX,
                        amount=TMG_GROUP_50_USD_AMOUNT,
                        type=str(DiscountType.PARTY_OF_FOUR),
                        used=False,
                    )
                )
            else:
                owner_discount.gift_codes.append(
                    DiscountGiftCodeModel(
                        code=TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX,
                        amount=look_price * TMG_GROUP_25_PERCENT_OFF,
                        type=str(DiscountType.PARTY_OF_FOUR),
                        used=False,
                    )
                )

    def get_gift_discount_intents_for_product_variant(self, variant_id: str) -> List[DiscountModel]:
        discounts = Discount.query.filter(
            Discount.shopify_virtual_product_variant_id == variant_id,
            Discount.shopify_discount_code == None,
            Discount.type == DiscountType.GIFT,
        ).all()

        return [DiscountModel.model_validate(discount) for discount in discounts]

    def mark_discount_by_shopify_code_as_paid(self, shopify_code: str) -> Optional[DiscountModel]:
        discount = Discount.query.filter(Discount.shopify_discount_code == shopify_code).first()

        if not discount:
            return None

        discount.used = True
        discount.updated_at = datetime.now(timezone.utc)
        db.session.add(discount)
        db.session.commit()

        return DiscountModel.model_validate(discount)

    def create_discount_intents(
        self, event_id: uuid.UUID, discount_intents: List[CreateDiscountIntent]
    ) -> DiscountPayResponseModel:
        if not discount_intents:
            raise BadRequestError("No discount intents provided.")

        event = self.event_service.get_event_by_id(event_id)

        if not event or not event.is_active:
            raise NotFoundError("Event not found.")

        attendees = {}

        for intent in discount_intents:
            attendee = self.attendee_service.get_attendee_by_id(intent.attendee_id)
            attendees[attendee.id] = attendee

            if not attendee.style:
                raise BadRequestError("Attendee is not styled.")

            if not attendee.invite:
                raise BadRequestError("Attendee is not invited.")

            if not attendee.look_id:
                raise BadRequestError("Attendee has no look associated.")

        num_attendees = self.attendee_service.get_num_discountable_attendees_for_event(event_id)
        existing_discounts = self.get_discounts_for_event(event_id)
        discounts_without_codes = self.__filter_discounts_without_codes(existing_discounts)

        intents = []
        total_intent_amount = 0
        shopify_products_to_remove = set()

        created_discounts = []

        for intent in discount_intents:
            attendee = attendees.get(intent.attendee_id)
            look = self.look_service.get_look_by_id(attendee.look_id)
            look_price = self.look_service.get_look_price(look)

            already_paid_discount_amount = 0

            for discount in existing_discounts:
                if (
                    discount.attendee_id == attendee.id
                    and discount.shopify_discount_code is not None
                    and discount.type == DiscountType.GIFT
                ):
                    already_paid_discount_amount += discount.amount

            tmg_group_discount = 0

            if num_attendees >= 4:
                if look_price <= TMG_MIN_SUIT_PRICE_FOR_25_PERCENT_OFF:
                    tmg_group_discount = TMG_GROUP_50_USD_AMOUNT
                else:
                    tmg_group_discount = look_price * TMG_GROUP_25_PERCENT_OFF

            if already_paid_discount_amount + intent.amount + tmg_group_discount > look_price:
                raise BadRequestError("Pay amount exceeds look price")

        try:
            for discount in discounts_without_codes:
                if discount.shopify_virtual_product_variant_id:
                    shopify_products_to_remove.add(discount.shopify_virtual_product_id)

                db.session.delete(discount)

            for intent in discount_intents:
                attendee = attendees.get(intent.attendee_id)

                total_intent_amount += intent.amount

                discount_intent = Discount(
                    event_id=event_id, attendee_id=attendee.id, amount=intent.amount, type=DiscountType.GIFT
                )

                intents.append(discount_intent)

                db.session.add(discount_intent)

            db.session.commit()

            for shopify_product_id in shopify_products_to_remove:
                try:
                    self.shopify_service.delete_product(ShopifyService.product_gid(shopify_product_id))
                except Exception as e:
                    # do not raise exception if shopify product deletion fails
                    pass
        except ServiceError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to persist discount intents.", e)

        for intent in intents:
            db.session.refresh(intent)

        try:
            product_body = "<strong>Groom gift discounts:</strong>"
            product_body += "<ul>"

            for intent in intents:
                attendee_user = self.user_service.get_user_for_attendee(intent.attendee_id)
                product_body += (
                    f"<li>Gift for {attendee_user.first_name} {attendee_user.last_name}: ${intent.amount}</li>"
                )

            product_body += "</ul>"

            shopify_product: ShopifyProduct = self.shopify_service.create_attendee_discount_product(
                title=f"{event.name} attendees discount",
                body_html=product_body,
                amount=total_intent_amount,
                sku=f"{DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{str(event.id)}-{datetime.now(timezone.utc).isoformat()}",
                tags=["hidden", "event_id=" + str(event.id), "user_id=" + str(event.user_id)],
            )

            for discount_intent in intents:
                discount_intent.shopify_virtual_product_id = shopify_product.get_id()
                discount_intent.shopify_virtual_product_variant_id = shopify_product.variants[0].get_id()
                db.session.add(discount_intent)

            db.session.commit()
        except Exception as e:
            # remove newly created discount intents if shopify product creation fails
            for discount in created_discounts:
                db.session.delete(discount)

            db.session.commit()

            raise ServiceError("Failed to create discount product in Shopify.", e)

        return DiscountPayResponseModel(variant_id=shopify_product.variants[0].get_id())

    def __filter_discounts_without_codes(self, discounts: List[Discount]) -> List[Discount]:
        return [
            discount
            for discount in discounts
            if not discount.shopify_discount_code and discount.type == DiscountType.GIFT
        ]

    def add_code_to_discount(self, discount_id: uuid.UUID, shopify_discount_id: uuid.UUID, code: str) -> DiscountModel:
        discount = self.get_discount_by_id(discount_id)
        discount.shopify_discount_code = code
        discount.shopify_discount_code_id = shopify_discount_id
        discount.updated_at = datetime.now(timezone.utc)

        db.session.add(discount)
        db.session.commit()

        return DiscountModel.model_validate(discount)

    def get_group_discount_for_attendee(self, attendee_id: uuid.UUID) -> Optional[DiscountModel]:
        discount = Discount.query.filter(
            Discount.attendee_id == attendee_id,
            Discount.type == DiscountType.PARTY_OF_FOUR,
        ).first()

        if not discount:
            return None

        return DiscountModel.model_validate(discount)

    def create_tmg_group_discount_for_attendee(self, attendee: AttendeeModel, event_id: uuid.UUID) -> DiscountModel:
        if not attendee.look_id:
            raise NotFoundError("Attendee has no look associated.")

        look = self.look_service.get_look_by_id(attendee.look_id)

        if not look or not look.product_specs or not look.product_specs.get("bundle", {}).get("variant_id"):
            raise ServiceError("Look has no bundle associated")

        event = self.event_service.get_event_by_id(event_id)
        look_price = self.look_service.get_look_price(look)
        attendee_user = self.user_service.get_user_for_attendee(attendee.id)

        if look_price <= TMG_MIN_SUIT_PRICE_FOR_25_PERCENT_OFF:
            code = f"{TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 999999)}"
            discount_amount = TMG_GROUP_50_USD_AMOUNT
        else:
            code = f"{TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 999999)}"
            discount_amount = look_price * TMG_GROUP_25_PERCENT_OFF

        title = code

        if look_price <= TMG_MIN_SUIT_PRICE_FOR_25_PERCENT_OFF:
            shopify_discount = self.shopify_service.create_discount_code(
                title,
                code,
                attendee_user.shopify_id,
                DiscountAmountType.FIXED_AMOUNT,
                TMG_GROUP_50_USD_AMOUNT,
                TMG_MIN_SUIT_PRICE,
            )
        else:
            shopify_discount = self.shopify_service.create_discount_code(
                title,
                code,
                attendee_user.shopify_id,
                DiscountAmountType.PERCENTAGE,
                TMG_GROUP_25_PERCENT_OFF,
                TMG_MIN_SUIT_PRICE_FOR_25_PERCENT_OFF,
            )

        discount = Discount(
            attendee_id=attendee.id,
            event_id=event_id,
            type=DiscountType.PARTY_OF_FOUR,
            amount=discount_amount,
            shopify_discount_code=shopify_discount.get("shopify_discount_code"),
            shopify_discount_code_id=shopify_discount.get("shopify_discount_id"),
        )
        db.session.add(discount)
        db.session.commit()

        return DiscountModel.model_validate(discount)

    def apply_discounts(self, attendee_id: uuid.UUID, shopify_cart_id: str) -> List[str]:
        attendee = self.attendee_service.get_attendee_by_id(attendee_id)

        if not attendee:
            raise NotFoundError("Attendee not found.")

        discounts = self.user_service.get_gift_paid_but_not_used_discounts(attendee_id)
        num_attendees = self.attendee_service.get_num_discountable_attendees_for_event(attendee.event_id)

        if num_attendees >= 4:
            existing_discount = self.get_group_discount_for_attendee(attendee_id)

            if not existing_discount:
                discount = self.create_tmg_group_discount_for_attendee(attendee, attendee.event_id)
                discounts.append(discount)
            else:
                discounts.append(existing_discount)

        if not discounts:
            return []

        self.shopify_service.apply_discount_codes_to_cart(
            shopify_cart_id, [discount.shopify_discount_code for discount in discounts]
        )

        return [discount.shopify_discount_code for discount in discounts]

    def get_discount_codes_for_attendees(
        self, attendee_ids: Set[uuid.UUID], type: DiscountType = None
    ) -> Dict[uuid.UUID, List[DiscountGiftCodeModel]]:
        discounts_query = Discount.query.filter(
            Discount.attendee_id.in_(attendee_ids), Discount.shopify_discount_code != None
        )
        if type:
            discounts_query = discounts_query.filter(Discount.type == type)

        discounts = discounts_query.all()
        attendee_discounts = {}

        for discount in discounts:
            if discount.attendee_id not in attendee_discounts:
                attendee_discounts[discount.attendee_id] = []

            attendee_discounts[discount.attendee_id].append(
                DiscountGiftCodeModel(
                    code=discount.shopify_discount_code,
                    amount=discount.amount,
                    type=str(discount.type),
                    used=discount.used,
                )
            )

        return attendee_discounts
