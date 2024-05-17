import random
from datetime import datetime, timezone

from server.database.database_manager import db
from server.database.models import Discount, Event, Attendee, DiscountType, User, Look
from server.flask_app import FlaskApp
from server.services import ServiceError, NotFoundError, BadRequestError
from server.services.attendee import AttendeeService
from server.services.shopify import ShopifyService, FakeShopifyService


class DiscountService:
    def __init__(self):
        super().__init__()

        if FlaskApp.current().config["TMG_APP_TESTING"]:
            self.shopify_service = FakeShopifyService()
        else:
            self.shopify_service = ShopifyService()

    def get_groom_gift_discounts(self, event_id):
        event = Event.query.filter(Event.id == event_id, Event.is_active).first()

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
            Discount.type == DiscountType.GROOM_GIFT,
            Discount.code == None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for discount_intent in discount_intents:
            groom_gift_discounts[discount_intent.attendee_id]["amount"] = discount_intent.amount

        paid_discounts = Discount.query.filter(
            Discount.event_id == event_id,
            Discount.type == DiscountType.GROOM_GIFT,
            Discount.code != None,
            Discount.attendee_id.in_(attendee_ids),
        ).all()

        for paid_discount in paid_discounts:
            groom_gift_discounts[paid_discount.attendee_id]["codes"].append(
                {"code": paid_discount.code, "amount": paid_discount.amount, "used": paid_discount.used}
            )

        return list(groom_gift_discounts.values())

    def get_groom_gift_discount_intents_for_product(self, product_id):
        return Discount.query.filter(
            Discount.shopify_virtual_product_id == str(product_id),
            Discount.code == None,
            Discount.type == DiscountType.GROOM_GIFT,
        ).all()

    def get_discount_by_shopify_code(self, shopify_code):
        return Discount.query.filter(Discount.code == shopify_code).first()

    def mark_discount_by_shopify_code_as_paid(self, shopify_code):
        discount = Discount.query.filter(Discount.code == shopify_code).first()

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

        event = Event.query.filter(Event.id == event_id, Event.is_active).first()

        if not event:
            raise NotFoundError("Event not found.")

        intents = []
        total_intent_amount = 0
        shopify_products_to_remove = set()

        created_discounts = []

        try:
            existing_discounts = Discount.query.filter(
                Discount.event_id == event_id,
                Discount.code == None,
                Discount.type == DiscountType.GROOM_GIFT,
            ).all()

            for discount in existing_discounts:
                if discount.shopify_virtual_product_id:
                    shopify_products_to_remove.add(discount.shopify_virtual_product_id)

                db.session.delete(discount)

            for intent in discount_intents:
                attendee = Attendee.query.filter(Attendee.id == intent["attendee_id"]).first()

                if not attendee:
                    raise NotFoundError(f"Attendee not found.")

                if intent["amount"] <= 0:
                    raise BadRequestError("Discount amount must be greater than 0.")

                total_intent_amount = total_intent_amount + float(intent["amount"])

                discount_intent = Discount(
                    event_id=event_id,
                    attendee_id=intent["attendee_id"],
                    amount=intent["amount"],
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
                discount_intent.shopify_virtual_product_id = str(shopify_product["id"])
                discount_intent.shopify_virtual_product_variant_id = str(shopify_product["variants"][0]["id"])
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
        discount = Discount.query.filter(Discount.id == discount_id).first()

        if not discount:
            raise NotFoundError("Discount not found.")

        discount.code = code
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
        attendee_service = AttendeeService()
        attendee_user = attendee_service.get_attendee_user(attendee_id)

        code = f"TMG-GROUP-100OFF-{random.randint(100000, 999999)}"
        title = code

        shopify_discount = self.shopify_service.create_discount_code2(title, code, attendee_user.shopify_id, 100)

        discount = Discount(
            attendee_id=attendee_id,
            event_id=event_id,
            type=DiscountType.PARTY_OF_FOUR,
            amount=100,
            code=shopify_discount.get("code"),
            shopify_discount_code_id=shopify_discount.get("shopify_discount_id"),
        )
        db.session.add(discount)
        db.session.commit()

        return discount
