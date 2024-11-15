import base64
import logging
import os
import random
import time
import uuid
from datetime import datetime

from sqlalchemy import text, select, func

from server.database.database_manager import db
from server.database.models import Look, Attendee
from server.flask_app import FlaskApp
from server.models.look_model import CreateLookModel, LookModel, UpdateLookModel
from server.models.shopify_model import ShopifyVariantModel
from server.services import ServiceError, DuplicateError, NotFoundError, BadRequestError
from server.services.integrations.aws_service import AbstractAWSService
from server.services.integrations.shopify_service import ShopifyService, AbstractShopifyService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)

DATA_BUCKET = os.environ.get("DATA_BUCKET", "data-bucket")
TMP_DIR = os.environ.get("TMPDIR", "/tmp")
BUY_NOW_COLLECTION_ID = os.environ.get("buy_now_suit_collection_id", "gid://shopify/Collection/1234567890")


class LookService:
    def __init__(
        self,
        user_service: UserService,
        aws_service: AbstractAWSService | None,
        shopify_service: AbstractShopifyService | None,
    ):
        self.user_service = user_service
        self.aws_service = aws_service
        self.shopify_service = shopify_service

    @staticmethod
    def get_look_by_id(look_id: uuid.UUID) -> LookModel:
        db_look = db.session.execute(select(Look).where(Look.id == look_id)).scalar_one_or_none()

        if not db_look:
            raise NotFoundError("Look not found")

        return LookModel.model_validate(db_look)

    def get_looks_by_user_id(self, user_id: uuid.UUID) -> list[LookModel]:
        look_models = [
            LookModel.model_validate(look)
            for look in db.session.execute(
                select(Look).where(Look.user_id == user_id, Look.is_active).order_by(Look.created_at.asc())
            )
            .scalars()
            .all()
        ]

        for look_model in look_models:
            look_model.price = self.get_look_price(look_model)

        return look_models

    @staticmethod
    def get_looks_for_event(event_id: uuid.UUID) -> list[LookModel]:
        looks = (
            db.session.execute(
                select(Look)
                .join(Attendee, Look.id == Attendee.look_id)
                .where(Attendee.event_id == event_id, Attendee.is_active)
            )
            .scalars()
            .all()
        )

        return [LookModel.model_validate(look) for look in looks]

    @staticmethod
    def get_user_look_for_event(user_id: uuid.UUID, event_id: uuid.UUID) -> LookModel:
        attendee = db.session.execute(
            select(Attendee).where(Attendee.user_id == user_id, Attendee.event_id == event_id, Attendee.is_active)
        ).scalar_one_or_none()

        if not attendee:
            raise NotFoundError("Attendee not found")

        look = db.session.execute(select(Look).where(Look.id == attendee.look_id)).scalar_one_or_none()

        if not look:
            raise NotFoundError("Look not found")

        return LookModel.model_validate(look)

    @staticmethod
    def get_look_price(look) -> float:
        bundle = look.product_specs.get("bundle", {})

        if not bundle:
            return 0.0

        return bundle.get("variant_price", bundle.get("price", 0.0))

    @staticmethod
    def __persist_new_look_to_db(create_look: CreateLookModel) -> Look:
        look = Look(
            id=uuid.uuid4(),
            name=create_look.name,
            user_id=create_look.user_id,
            product_specs=create_look.product_specs,
            image_path=None,
            is_active=create_look.is_active,
        )
        db.session.add(look)
        return look

    @staticmethod
    def __verify_if_look_exist(create_look: CreateLookModel) -> None:
        db_look = db.session.execute(
            select(Look).where(Look.name == create_look.name, Look.user_id == create_look.user_id, Look.is_active)
        ).scalar_one_or_none()

        if db_look:
            raise DuplicateError("Look already exists with that name.")

    def __store_look_image_to_s3(self, create_look: CreateLookModel, db_look: Look) -> str:
        timestamp = str(int(time.time() * 1000))
        local_file = f"{TMP_DIR}/{timestamp}.png"
        s3_file = f"looks/{create_look.user_id}/{db_look.id}/{timestamp}.png"

        self.__save_image(create_look.image, local_file)
        self.aws_service.upload_to_s3(local_file, DATA_BUCKET, s3_file)

        return s3_file

    @staticmethod
    def __get_suit_parts_by_sku(suit_sku: str) -> list[str]:
        if not suit_sku:
            raise ServiceError("Suit variant sku not found.")

        if not suit_sku.startswith("00"):
            raise ServiceError(f"Invalid suit variant sku: {suit_sku}")

        jacket_sku = "1" + suit_sku[1:]

        if suit_sku == "002A2BLK":  # HACK! tuxedo has same pants and vest as black suit
            pants_sku = "201" + suit_sku[3:]
            vest_sku = "301" + suit_sku[3:]
        else:
            pants_sku = "2" + suit_sku[1:]
            vest_sku = "3" + suit_sku[1:]

        return [jacket_sku, pants_sku, vest_sku]

    def __get_suit_parts(self, suit_variant_id: str) -> list[ShopifyVariantModel]:
        suit_variants: list[ShopifyVariantModel] = self.shopify_service.get_variants_by_id([suit_variant_id])

        if not suit_variants or len(suit_variants) == 0 or not suit_variants[0]:
            raise ServiceError("Suit variant not found.")

        suit_variant = suit_variants[0]
        suit_sku = suit_variant.variant_sku

        if not suit_sku:
            raise ServiceError("Suit variant sku not found.")

        if not suit_sku.startswith("00"):
            raise ServiceError(f"Invalid suit variant sku: {suit_variant}")

        jacket_sku = "1" + suit_sku[1:]

        if suit_sku == "002A2BLK":  # HACK! tuxedo has same pants and vest as black suit
            pants_sku = "201" + suit_sku[3:]
            vest_sku = "301" + suit_sku[3:]
        else:
            pants_sku = "2" + suit_sku[1:]
            vest_sku = "3" + suit_sku[1:]

        jacket_variant = self.shopify_service.get_variant_by_sku(jacket_sku)
        pants_variant = self.shopify_service.get_variant_by_sku(pants_sku)
        vest_variant = self.shopify_service.get_variant_by_sku(vest_sku)

        if not jacket_variant or not pants_variant or not vest_variant:
            raise ServiceError("Not all suit parts were found.")

        return [jacket_variant, pants_variant, vest_variant]

    @staticmethod
    def __enrich_product_specs_variants_with_suit_parts(
        suit_variant_id: str,
        product_spec_variants: list[str],
        suit_parts_variants: list[ShopifyVariantModel],
    ) -> list[str]:
        enriched_product_specs_variants = product_spec_variants.copy()
        enriched_product_specs_variants.remove(suit_variant_id)

        enriched_product_specs_variants = [
            variant.variant_id for variant in suit_parts_variants
        ] + enriched_product_specs_variants

        return enriched_product_specs_variants

    def __create_id_based_look(self, create_look: CreateLookModel) -> LookModel:
        db_look = self.__persist_new_look_to_db(create_look)
        s3_file = self.__store_look_image_to_s3(create_look, db_look) if create_look.image else None

        suit_variant_id = create_look.product_specs.get("suit_variant")

        if not suit_variant_id:
            raise ServiceError("Suit variant id is missing.")

        bundle_id = str(random.randint(100000, 1000000000))

        bundle_identifier_variant_id = str(
            self.shopify_service.create_bundle_identifier_product(bundle_id).variants[0].get_id()
        )

        enriched_look_variants = create_look.product_specs.get("variants") + [bundle_identifier_variant_id]

        look_variants = self.shopify_service.get_variants_by_id(enriched_look_variants)

        suit_parts_variants = self.__get_suit_parts(suit_variant_id)

        all_variants = look_variants + suit_parts_variants

        tags = self.__get_tags_from_look_variants(all_variants)
        tags.append("suit_bundle")

        id_to_variants = {variant.variant_id: variant for variant in all_variants}

        enriched_product_specs_variants = self.__enrich_product_specs_variants_with_suit_parts(
            suit_variant_id,
            enriched_look_variants,
            suit_parts_variants,
        )

        bundle_product_variant_id = self.shopify_service.create_bundle(
            f'Bundle "{create_look.name}"',
            bundle_id,
            enriched_product_specs_variants,
            image_src=(f"https://{FlaskApp.current().images_data_endpoint_host}/{s3_file}" if s3_file else None),
            tags=tags,
        )

        if not bundle_product_variant_id:
            raise ServiceError("Failed to create bundle product variant.")

        bundle_product_variant = self.shopify_service.get_variants_by_id([bundle_product_variant_id])[0]

        enriched_product_specs = {
            "bundle": bundle_product_variant.model_dump(),
            "suit": id_to_variants[suit_variant_id].model_dump(),
            "items": [id_to_variants[variant_id].model_dump() for variant_id in enriched_product_specs_variants],
        }

        db_look.image_path = s3_file
        db_look.product_specs = enriched_product_specs

        db.session.commit()
        db.session.refresh(db_look)

        return db_look

    def __create_sku_based_look(self, create_look: CreateLookModel, is_buy_now: bool = False) -> LookModel:
        db_look = self.__persist_new_look_to_db(create_look)
        s3_file = self.__store_look_image_to_s3(create_look, db_look) if create_look.image else None

        suit_sku = create_look.product_specs.get("suit")

        if not suit_sku:
            raise ServiceError("Suit sku is missing.")

        bundle_id = str(random.randint(100000, 1000000000))
        bundle_identifier_variant = self.shopify_service.create_bundle_identifier_product(bundle_id).variants[0]

        bundle_items = set(create_look.product_specs.get("items"))
        bundle_items.discard(suit_sku)
        suit_parts_skus = self.__get_suit_parts_by_sku(suit_sku)
        all_skus = list(bundle_items) + suit_parts_skus

        tags = self.__get_tags_from_look_variants2(all_skus)
        tags.append("suit_bundle")
        tags.append("not_linked_to_event")

        variants = self.shopify_service.get_variants_by_skus(all_skus)
        variants = self.__filter_out_black_tuxedo_vs_black_suit_items(suit_sku, variants)

        bundle_variants = [look_variant.variant_id for look_variant in variants]
        bundle_variants.append(str(bundle_identifier_variant.get_id()))

        bundle = self.shopify_service.create_bundle2(
            f'Bundle "{create_look.name}"',
            bundle_id,
            bundle_variants,
            image_src=(f"https://{FlaskApp.current().images_data_endpoint_host}/{s3_file}" if s3_file else None),
            tags=tags,
        )

        if is_buy_now:
            self.shopify_service.add_products_to_collection(int(BUY_NOW_COLLECTION_ID), [int(bundle.product_id)])

        if not bundle:
            raise ServiceError("Failed to create bundle.")

        all_skus.append(bundle_identifier_variant.sku)

        enriched_product_specs = {
            "bundle": {
                "sku": bundle.variant_sku,
                "product_id": bundle.product_id,
                "variant_id": bundle.variant_id,
                "price": bundle.variant_price,
            },
            "suit": {"sku": suit_sku},
            "items": [{"sku": sku} for sku in all_skus],
        }

        db_look.image_path = s3_file
        db_look.product_specs = enriched_product_specs

        db.session.commit()
        db.session.refresh(db_look)

        return db_look

    def __filter_out_black_tuxedo_vs_black_suit_items(
        self,
        suit_sku: str,
        variants: list[ShopifyVariantModel],
    ) -> list[ShopifyVariantModel]:
        # HACK! tuxedo has same pants and vest as black suit
        if suit_sku not in (
            "001A2BLK",  # Black Suit
            "002A2BLK",  # Black Tuxedo
        ):
            return variants

        suit_parts = self.__get_suit_parts_by_sku(suit_sku)
        suit_pants = suit_parts[1]
        suit_vest = suit_parts[2]

        result = []

        if suit_sku == "001A2BLK":  # Black Suit
            for variant in variants:
                if variant.variant_sku in (suit_pants, suit_vest) and "Tuxedo" in variant.product_title:
                    continue

                result.append(variant)
        elif suit_sku == "002A2BLK":  # Black Tuxedo
            for variant in variants:
                if variant.variant_sku in (suit_pants, suit_vest) and "Tuxedo" not in variant.product_title:
                    continue

                result.append(variant)
        else:
            result = variants

        return result

    def create_look(self, create_look: CreateLookModel, is_buy_now: bool = False) -> LookModel:
        self.__verify_if_look_exist(create_look)

        try:
            if "variants" in create_look.product_specs:
                db_look = self.__create_id_based_look(create_look)
            else:
                db_look = self.__create_sku_based_look(create_look, is_buy_now)
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to create look.", e)

        return LookModel.model_validate(db_look)

    @staticmethod
    def update_look(look_id: uuid.UUID, update_look: UpdateLookModel) -> LookModel:
        db_look = db.session.execute(select(Look).where(Look.id == look_id)).scalar_one_or_none()

        if not db_look:
            raise NotFoundError("Look not found")

        existing_look = db.session.execute(
            select(Look).where(Look.name == update_look.name, Look.user_id == db_look.user_id, Look.id != look_id)
        ).scalar_one_or_none()

        if existing_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            db_look.name = update_look.name
            db_look.product_specs = update_look.product_specs
            db_look.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(db_look)
        except Exception as e:
            raise ServiceError("Failed to update look.", e)

        return LookModel.model_validate(db_look)

    def delete_look(self, look_id: uuid.UUID) -> None:
        look = db.session.execute(select(Look).where(Look.id == look_id)).scalar_one_or_none()

        if not look:
            raise NotFoundError("Look not found")

        num_attendees = db.session.execute(
            select(func.count(Attendee.id)).where(Attendee.look_id == look_id, Attendee.is_active)
        ).scalar()

        if num_attendees > 0:
            raise BadRequestError("Can't delete look associated with attendee")

        try:
            look.is_active = False
            look.updated_at = datetime.now()

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete look.", e)

        self.__archive_suit_bundle(look.product_specs)

    def __archive_suit_bundle(self, product_specs: dict) -> None:
        if not product_specs:
            return

        product_id = product_specs.get("bundle", {}).get("product_id")

        if not product_id:
            logger.warning(f"Product spec {product_specs} does not have a bundle.product_id")
            return

        items = product_specs.get("items", [])

        if not items:
            logger.warning(f"Product spec {product_specs} does not have any items")
            self.shopify_service.archive_product(ShopifyService.product_gid(product_id))
            return

        has_bundle_identifier_product = False
        bundle_identifier_product_id = None

        for item in items:
            sku = item.get("variant_sku", item.get("sku"))
            bundle_identifier_product_id = item.get("product_id")

            if not sku:
                continue

            if sku.startswith("bundle-"):
                bundle_identifier_product = self.shopify_service.get_variant_by_sku(sku)

                if not bundle_identifier_product:
                    continue

                bundle_identifier_product_id = bundle_identifier_product.product_id
                has_bundle_identifier_product = True
                break

        self.shopify_service.archive_product(ShopifyService.product_gid(product_id))

        if has_bundle_identifier_product:
            self.shopify_service.archive_product(ShopifyService.product_gid(bundle_identifier_product_id))

    @staticmethod
    def __save_image(image_b64: str, local_file: str) -> None:
        try:
            image_b64 = image_b64.replace("data:image/png;base64,", "")
            decoded_image = base64.b64decode(image_b64)

            with open(local_file, "wb") as f:
                f.write(decoded_image)
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to save image.", e)

    @staticmethod
    def find_look_by_item_sku(sku: str) -> LookModel | None:
        query = text(
            f"""
            SELECT id, name, user_id, product_specs, image_path, is_active
            FROM looks 
            WHERE product_specs->'items' IS NOT NULL 
              AND json_typeof(product_specs->'items') = 'array' 
              AND EXISTS (
                SELECT 1 
                FROM json_array_elements(product_specs->'items') AS item 
                WHERE item->>'sku' = '{sku}');
            """
        )

        rows = db.session.execute(query).fetchall()

        if not rows or len(rows) == 0:
            return None

        look_row = rows[0]

        return LookModel(
            id=look_row.id,
            name=look_row.name,
            user_id=look_row.user_id,
            product_specs=look_row.product_specs,
            image_path=look_row.image_path,
            is_active=look_row.is_active,
        )

    @staticmethod
    def __get_tags_from_look_variants(variants: list[ShopifyVariantModel]) -> list[str]:
        tags = set()

        for variant in variants:
            if not variant.variant_sku:
                continue

            if variant.variant_sku.startswith("4"):
                tags.add("has_shirt")
            elif variant.variant_sku.startswith("5"):
                tags.add("has_bow_tie")
                tags.add("has_tie")
            elif variant.variant_sku.startswith("6"):
                tags.add("has_tie")
                tags.add("has_neck_tie")
            elif variant.variant_sku.startswith("7"):
                tags.add("has_belt")
            elif variant.variant_sku.startswith("8"):
                tags.add("has_shoes")
            elif variant.variant_sku.startswith("9"):
                tags.add("has_socks")
            elif variant.variant_sku.startswith("P"):
                tags.add("has_premium_pocket_square")

        return list(tags)

    @staticmethod
    def __get_tags_from_look_variants2(skus: list[str]) -> list[str]:
        tags = set()

        for sku in skus:
            if not sku:
                continue

            if sku.startswith("4"):
                tags.add("has_shirt")
            elif sku.startswith("5"):
                tags.add("has_bow_tie")
                tags.add("has_tie")
            elif sku.startswith("6"):
                tags.add("has_tie")
                tags.add("has_neck_tie")
            elif sku.startswith("7"):
                tags.add("has_belt")
            elif sku.startswith("8"):
                tags.add("has_shoes")
            elif sku.startswith("9"):
                tags.add("has_socks")
            elif sku.startswith("P"):
                tags.add("has_premium_pocket_square")

        return list(tags)
