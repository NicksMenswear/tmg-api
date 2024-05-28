import random
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_

from server.database.database_manager import db
from server.database.models import Discount, Attendee, DiscountType, User, Look
from server.models.attendee_model import AttendeeModel
from server.models.discount_model import (
    DiscountModel,
    CreateDiscountIntent,
    EventDiscountModel,
    EventDiscountLookModel,
    EventDiscountCodeModel,
    CreateDiscountIntentPayFull,
)
from server.services import ServiceError, NotFoundError, BadRequestError
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.look import LookService
from server.services.shopify import AbstractShopifyService
from server.services.user import UserService

GROOM_DISCOUNT_TYPES = {DiscountType.GROOM_GIFT, DiscountType.GROOM_FULL_PAY}
GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX = "GROOM-DISCOUNT"
GROOM_GIFT_DISCOUNT_CODE_PREFIX = "GROOM-GIFT"
TMG_GROUP_DISCOUNT_CODE_PREFIX = "TMG-GROUP-100-OFF"


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
            DiscountModel.from_orm(discount)
            for discount in Discount.query.filter(Discount.attendee_id == attendee_id).all()
        ]

    def get_discount_by_shopify_code(self, shopify_code: str) -> Optional[DiscountModel]:
        discount = Discount.query.filter(Discount.shopify_discount_code == shopify_code).first()

        if not discount:
            return None

        return DiscountModel.from_orm(discount)

    def create_discount(
        self,
        event_id,
        attendee_id,
        amount,
        discount_type=DiscountType.GROOM_GIFT,
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

    def get_gift_discounts(self, event_id: UUID) -> List[EventDiscountModel]:
        event = self.event_service.get_event_by_id(event_id)

        if not event:
            raise NotFoundError("Event not found.")

        users_attendees_looks = (
            db.session.query(User, Attendee, Look)
            .join(Attendee, User.id == Attendee.attendee_id)
            .outerjoin(Look, Attendee.look_id == Look.id)
            .filter(Attendee.event_id == event_id, Attendee.is_active)
            .all()
        )

        if not users_attendees_looks:
            return []

        gift_discounts = {}

        attendee_ids = []

        for user, attendee, look in users_attendees_looks:
            attendee_ids.append(attendee.id)

            gift_discounts[attendee.id] = EventDiscountModel(
                attendee_id=attendee.id,
                event_id=event_id,
                first_name=user.first_name,
                last_name=user.last_name,
                amount=0,
                codes=[],
                look=EventDiscountLookModel(id=attendee.look_id, name=look.look_name, price=0) if look else None,
            )

            if look and look.product_specs and look.product_specs.get("variants"):
                variant_ids = look.product_specs["variants"]
                look_price = self.shopify_service.get_total_price_for_variants(variant_ids)
                gift_discounts[attendee.id].look.price = look_price

        discount_intents = Discount.query.filter(
            Discount.event_id == event_id,
            or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
            Discount.shopify_discount_code == None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for discount_intent in discount_intents:
            gift_discounts[discount_intent.attendee_id].amount = discount_intent.amount

        paid_discounts = Discount.query.filter(
            Discount.event_id == event_id,
            or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
            Discount.shopify_discount_code != None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for paid_discount in paid_discounts:
            gift_discounts[paid_discount.attendee_id].codes.append(
                EventDiscountCodeModel(
                    code=paid_discount.shopify_discount_code,
                    amount=paid_discount.amount,
                    type=str(paid_discount.type),
                    used=paid_discount.used,
                )
            )

        return list(gift_discounts.values())

    def get_gift_discount_intents_for_product(self, product_id: str) -> List[DiscountModel]:
        discounts = Discount.query.filter(
            Discount.shopify_virtual_product_id == product_id,
            Discount.shopify_discount_code == None,
            or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
        ).all()

        return [DiscountModel.from_orm(discount) for discount in discounts]

    def mark_discount_by_shopify_code_as_paid(self, shopify_code: str) -> Optional[DiscountModel]:
        discount = Discount.query.filter(Discount.shopify_discount_code == shopify_code).first()

        if not discount:
            return None

        discount.used = True
        discount.updated_at = datetime.now(timezone.utc)
        db.session.add(discount)
        db.session.commit()

        return DiscountModel.from_orm(discount)

    def create_discount_intents(
        self,
        event_id: uuid.UUID,
        discount_intents: List[CreateDiscountIntent],
    ) -> List[DiscountModel]:
        if not discount_intents:
            return []

        event = self.event_service.get_event_by_id(event_id)

        if not event or not event.is_active:
            raise NotFoundError("Event not found.")

        num_attendees = self.event_service.get_num_attendees_for_event(event_id)
        existing_discounts = self.get_discounts_for_event(event_id)
        discounts_without_codes = self.__filter_groom_discounts_without_codes(existing_discounts)

        intents = []
        total_intent_amount = 0
        shopify_products_to_remove = set()

        created_discounts = []

        try:
            for discount in discounts_without_codes:
                if discount.shopify_virtual_product_id:
                    shopify_products_to_remove.add(discount.shopify_virtual_product_id)

                db.session.delete(discount)

            for intent in discount_intents:
                attendee = self.attendee_service.get_attendee_by_id(intent.attendee_id)
                attendee_discounts = self.__filter_attendee_discounts(existing_discounts, attendee.id)

                if isinstance(intent, CreateDiscountIntentPayFull):
                    if any(discount.shopify_discount_code for discount in attendee_discounts):
                        raise BadRequestError(f"Groom gift discount already issued for attendee '{attendee.id}'")

                    look = self.look_service.get_look_by_id(attendee.look_id)

                    if not look:
                        raise NotFoundError("Look not found.")

                    if not look.product_specs or len(look.product_specs.get("variants", [])) == 0:
                        raise BadRequestError("Look has no variants.")

                    total_price_of_look = self.shopify_service.get_total_price_for_variants(
                        look.product_specs.get("variants")
                    )

                    total_intent_amount += total_price_of_look

                    if total_price_of_look < 100:
                        raise BadRequestError("Total look items price must be greater than 100.")

                    if num_attendees >= 4:
                        total_intent_amount -= 100

                    discount_intent = Discount(
                        event_id=event_id,
                        attendee_id=attendee.id,
                        amount=total_price_of_look,
                        type=DiscountType.GROOM_FULL_PAY,
                    )

                    intents.append(discount_intent)
                else:
                    if any(
                        discount.shopify_discount_code and discount.type == DiscountType.GROOM_FULL_PAY
                        for discount in attendee_discounts
                    ):
                        raise BadRequestError(
                            f"Groom full pay gift discount already issued for attendee '{attendee.id}'"
                        )

                    total_intent_amount += intent.amount

                    discount_intent = Discount(
                        event_id=event_id,
                        attendee_id=attendee.id,
                        amount=intent.amount,
                        type=DiscountType.GROOM_GIFT,
                    )

                    intents.append(discount_intent)

                db.session.add(discount_intent)

            db.session.commit()

            for shopify_product_id in shopify_products_to_remove:
                try:
                    self.shopify_service.delete_product(shopify_product_id)
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
                type = "Full pay" if intent.type == DiscountType.GROOM_FULL_PAY else "Gift"
                product_body += (
                    f"<li>{type} for {attendee_user.first_name} {attendee_user.last_name}: ${intent.amount}</li>"
                )

            if num_attendees >= 4:
                product_body += "<li>Group discount: -$100</li>"

            product_body += "</ul>"

            shopify_product = self.shopify_service.create_virtual_product(
                title=f"{event.event_name} attendees discount",
                body_html=product_body,
                price=total_intent_amount,
                sku=f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{str(event.id)}-{datetime.now(timezone.utc).isoformat()}",
                tags=",".join(
                    ["virtual", "groom_discount", "event_id=" + str(event.id), "user_id=" + str(event.user_id)]
                ),
            )

            for discount_intent in intents:
                discount_intent.shopify_virtual_product_id = shopify_product["id"]
                discount_intent.shopify_virtual_product_variant_id = shopify_product["variants"][0]["id"]
                db.session.add(discount_intent)

            db.session.commit()
        except Exception as e:
            # remove newly created discount intents if shopify product creation fails
            for discount in created_discounts:
                db.session.delete(discount)

            db.session.commit()

            raise ServiceError("Failed to create discount product in Shopify.", e)

        return [DiscountModel.from_orm(intent) for intent in intents]

    def __filter_groom_discounts_without_codes(self, discounts: List[Discount]) -> List[Discount]:
        return [
            discount
            for discount in discounts
            if not discount.shopify_discount_code and discount.type in GROOM_DISCOUNT_TYPES
        ]

    def __filter_attendee_discounts(self, discounts: List[Discount], attendee_id: uuid.UUID):
        return [discount for discount in discounts if discount.attendee_id == attendee_id]

    def add_code_to_discount(self, discount_id: uuid.UUID, shopify_discount_id: uuid.UUID, code: str) -> DiscountModel:
        discount = self.get_discount_by_id(discount_id)
        discount.shopify_discount_code = code
        discount.shopify_discount_code_id = shopify_discount_id
        discount.updated_at = datetime.now(timezone.utc)

        db.session.add(discount)
        db.session.commit()

        return DiscountModel.from_orm(discount)

    def get_group_discount_for_attendee(self, attendee_id: uuid.UUID) -> Optional[DiscountModel]:
        discount = Discount.query.filter(
            Discount.attendee_id == attendee_id,
            Discount.type == DiscountType.PARTY_OF_FOUR,
        ).first()

        if not discount:
            return None

        return DiscountModel.from_orm(discount)

    def create_tmg_group_discount_for_attendee(self, attendee: AttendeeModel, event_id: uuid.UUID) -> DiscountModel:
        if not attendee.look_id:
            raise NotFoundError("Attendee has no look associated.")

        look = self.look_service.get_look_by_id(attendee.look_id)

        if not look or not look.product_specs or len(look.product_specs.get("variants", [])) == 0:
            raise ServiceError("Look has no variants.")

        attendee_user = self.user_service.get_user_for_attendee(attendee.id)

        code = f"{TMG_GROUP_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 999999)}"
        title = code

        shopify_discount = self.shopify_service.create_discount_code(title, code, attendee_user.shopify_id, 100, [])

        discount = Discount(
            attendee_id=attendee.id,
            event_id=event_id,
            type=DiscountType.PARTY_OF_FOUR,
            amount=100,
            shopify_discount_code=shopify_discount.get("shopify_discount_code"),
            shopify_discount_code_id=shopify_discount.get("shopify_discount_id"),
        )
        db.session.add(discount)
        db.session.commit()

        return DiscountModel.from_orm(discount)

    def apply_discounts(self, attendee_id: uuid.UUID, event_id: uuid.UUID, shopify_cart_id: str) -> List[str]:
        attendee = self.attendee_service.get_attendee_by_id(attendee_id)

        if not attendee:
            raise NotFoundError("Attendee not found.")

        discounts = self.user_service.get_grooms_gift_paid_but_not_used_discounts(attendee_id)

        groom_full_pay_discount_types = set([discount.type for discount in discounts])
        can_apply_tmg_discount = False if DiscountType.GROOM_FULL_PAY in groom_full_pay_discount_types else True

        if can_apply_tmg_discount:
            num_attendees = self.event_service.get_num_attendees_for_event(event_id)

            if num_attendees >= 4:
                existing_discount = self.get_group_discount_for_attendee(attendee_id)

                if not existing_discount:
                    discount = self.create_tmg_group_discount_for_attendee(attendee, event_id)
                    discounts.append(discount)
                else:
                    discounts.append(existing_discount)

        discounts = [discount for discount in discounts]

        if not discounts:
            return []

        self.shopify_service.apply_discount_codes_to_cart(
            shopify_cart_id, [discount.shopify_discount_code for discount in discounts]
        )

        return [discount.shopify_discount_code for discount in discounts]
