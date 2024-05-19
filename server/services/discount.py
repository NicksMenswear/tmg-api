import random
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_

from server.database.database_manager import db
from server.database.models import Discount, Attendee, DiscountType, User, Look
from server.services import ServiceError, NotFoundError, BadRequestError
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.look import LookService
from server.services.shopify import AbstractShopifyService
from server.services.user import UserService


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

    def get_discount_by_id(self, discount_id):
        return Discount.query.filter(Discount.id == discount_id).first()

    def get_groom_gift_discounts(self, event_id: UUID):
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

        groom_gift_discounts = {}

        attendee_ids = []

        for user, attendee, look in users_attendees_looks:
            attendee_ids.append(attendee.id)

            groom_gift_discounts[attendee.id] = {
                "attendee_id": attendee.id,
                "event_id": event_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "amount": 0,
                "codes": [],
                "look": {"id": attendee.look_id, "name": look.look_name if look else None, "price": 0},
            }

            if look and look.product_specs and look.product_specs.get("variants"):
                variant_ids = look.product_specs["variants"]
                look_price = self.shopify_service.get_total_price_for_variants(variant_ids)
                groom_gift_discounts[attendee.id]["look"]["price"] = look_price

        discount_intents = Discount.query.filter(
            Discount.event_id == event_id,
            or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
            Discount.shopify_discount_code == None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for discount_intent in discount_intents:
            groom_gift_discounts[discount_intent.attendee_id]["amount"] = discount_intent.amount

        paid_discounts = Discount.query.filter(
            Discount.event_id == event_id,
            or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
            Discount.shopify_discount_code != None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for paid_discount in paid_discounts:
            groom_gift_discounts[paid_discount.attendee_id]["codes"].append(
                {
                    "code": paid_discount.shopify_discount_code,
                    "amount": paid_discount.amount,
                    "type": str(paid_discount.type),
                    "used": paid_discount.used,
                }
            )

        return list(groom_gift_discounts.values())

    def get_groom_gift_discount_intents_for_product(self, product_id):
        return Discount.query.filter(
            Discount.shopify_virtual_product_id == product_id,
            Discount.shopify_discount_code == None,
            or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
        ).all()

    def get_discount_by_shopify_code(self, shopify_code):
        return Discount.query.filter(Discount.shopify_discount_code == shopify_code).first()

    def mark_discount_by_shopify_code_as_paid(self, shopify_code):
        discount = Discount.query.filter(Discount.shopify_discount_code == shopify_code).first()

        if not discount:
            return None

        discount.used = True
        discount.updated_at = datetime.now(timezone.utc)
        db.session.add(discount)
        db.session.commit()

        return discount

    def create_groom_gift_discount_intents(self, event_id, discount_intents):
        if not discount_intents:
            return []

        event = self.event_service.get_event_by_id(event_id)

        if not event or not event.is_active:
            raise NotFoundError("Event not found.")

        num_attendees = self.event_service.get_num_attendees_for_event(event_id)

        intents = []
        total_intent_amount = 0
        shopify_products_to_remove = set()

        created_discounts = []

        try:
            existing_discounts = Discount.query.filter(
                Discount.event_id == event_id,
                Discount.shopify_discount_code == None,
                or_(Discount.type == DiscountType.GROOM_GIFT, Discount.type == DiscountType.GROOM_FULL_PAY),
            ).all()

            for discount in existing_discounts:
                if discount.shopify_virtual_product_id:
                    shopify_products_to_remove.add(discount.shopify_virtual_product_id)

                db.session.delete(discount)

            for intent in discount_intents:
                attendee = self.attendee_service.get_attendee_by_id(intent.get("attendee_id"))

                if not attendee:
                    raise NotFoundError(f"Attendee not found.")

                # TODO: refactor via pydantic validation
                if "pay_full" not in intent and "amount" not in intent:
                    raise BadRequestError("Either 'amount' or 'pay_full' must be provided for intent.")

                if intent.get("pay_full") and intent.get("amount"):
                    raise BadRequestError("'amount' shouldn't be present when 'pay_full' is set.")

                if "amount" in intent and intent.get("amount") <= 0:
                    raise BadRequestError("Discount amount must be greater than 0.")

                if intent.get("pay_full"):
                    look = self.look_service.get_look_by_id(attendee.look_id)

                    if not look:
                        raise NotFoundError("Look not found.")

                    if (
                        not look.product_specs
                        or not look.product_specs.get("variants")
                        or len(look.product_specs.get("variants")) == 0
                    ):
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
                        attendee_id=intent.get("attendee_id"),
                        amount=total_price_of_look,
                        type=DiscountType.GROOM_FULL_PAY,
                    )

                    intents.append(discount_intent)
                else:
                    total_intent_amount += intent.get("amount")

                    discount_intent = Discount(
                        event_id=event_id,
                        attendee_id=intent.get("attendee_id"),
                        amount=intent.get("amount"),
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
            shopify_product = self.shopify_service.create_virtual_product(
                title=f"{event.event_name} attendees discount",
                body_html=f"Discount for {event.event_name} event for ${total_intent_amount}",
                price=total_intent_amount,
                sku=f"GROOM-DISCOUNT-{str(event.id)}-{datetime.now(timezone.utc).isoformat()}",
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

        return intents

    def add_code_to_discount(self, discount_id, shopify_discount_id, code):
        discount = self.get_discount_by_id(discount_id)

        if not discount:
            raise NotFoundError("Discount not found.")

        discount.shopify_discount_code = code
        discount.shopify_discount_code_id = shopify_discount_id
        discount.updated_at = datetime.now(timezone.utc)

        db.session.add(discount)
        db.session.commit()

        return discount

    def get_group_discount_for_attendee(self, attendee_id):
        return Discount.query.filter(
            Discount.attendee_id == attendee_id,
            Discount.type == DiscountType.PARTY_OF_FOUR,
        ).first()

    def create_group_discount_for_attendee(self, attendee_id, event_id):
        attendee_user = self.attendee_service.get_attendee_user(attendee_id)

        code = f"TMG-GROUP-100-OFF-{random.randint(100000, 999999)}"
        title = code

        shopify_discount = self.shopify_service.create_discount_code(title, code, attendee_user.shopify_id, 100)

        discount = Discount(
            attendee_id=attendee_id,
            event_id=event_id,
            type=DiscountType.PARTY_OF_FOUR,
            amount=100,
            shopify_discount_code=shopify_discount.get("shopify_discount_code"),
            shopify_discount_code_id=shopify_discount.get("shopify_discount_id"),
        )
        db.session.add(discount)
        db.session.commit()

        return discount

    def apply_discounts(self, attendee_id, event_id, shopify_cart_id):
        discounts = self.user_service.get_grooms_gift_paid_but_not_used_discounts(attendee_id)

        num_attendees = self.event_service.get_num_attendees_for_event(event_id)

        if num_attendees >= 4:
            existing_discount = self.get_group_discount_for_attendee(attendee_id)

            if not existing_discount:
                discount = self.create_group_discount_for_attendee(attendee_id, event_id)
                discounts.append(discount)
            else:
                discounts.append(existing_discount)

        discounts = [discount for discount in discounts]

        if not discounts:
            return

        self.shopify_service.apply_discount_codes_to_cart(
            shopify_cart_id, [discount.shopify_discount_code for discount in discounts]
        )
