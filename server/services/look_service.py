import base64
import logging
import os
import random
import time
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import text

from server.database.database_manager import db
from server.database.models import Look, Attendee
from server.flask_app import FlaskApp
from server.models.look_model import CreateLookModel, LookModel, UpdateLookModel, ProductSpecType
from server.models.shopify_model import ShopifyVariantModel
from server.services import ServiceError, DuplicateError, NotFoundError, BadRequestError
from server.services.integrations.aws_service import AbstractAWSService
from server.services.integrations.shopify_service import AbstractShopifyService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)

DATA_BUCKET = os.environ.get("DATA_BUCKET", "data-bucket")
TMP_DIR = os.environ.get("TMPDIR", "/tmp")


# noinspection PyMethodMayBeStatic
class LookService:
    def __init__(
        self, user_service: UserService, aws_service: AbstractAWSService, shopify_service: AbstractShopifyService
    ):
        self.user_service = user_service
        self.aws_service = aws_service
        self.shopify_service = shopify_service

    def get_look_by_id(self, look_id: uuid.UUID) -> LookModel:
        db_look = Look.query.filter(Look.id == look_id).first()

        if not db_look:
            raise NotFoundError("Look not found")

        return LookModel.model_validate(db_look)

    def get_looks_by_user_id(self, user_id: uuid.UUID) -> List[LookModel]:
        look_models = [
            LookModel.model_validate(look)
            for look in Look.query.filter(Look.user_id == user_id, Look.is_active).order_by(Look.created_at.asc()).all()
        ]

        for look_model in look_models:
            look_model.price = self.get_look_price(look_model)

        return look_models

    def get_user_look_for_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> LookModel:
        attendee = Attendee.query.filter(Attendee.user_id == user_id, Attendee.event_id == event_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found")

        look = Look.query.filter(Look.id == attendee.look_id).first()

        if not look:
            raise NotFoundError("Look not found")

        return LookModel.model_validate(look)

    def get_look_price(self, look) -> float:
        return look.product_specs.get("bundle", {}).get("variant_price")

    def __persist_new_look_to_db(self, create_look: CreateLookModel) -> Look:
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

    def __verify_that_look_does_not_exist(self, create_look: CreateLookModel) -> None:
        db_look: Look = Look.query.filter(
            Look.name == create_look.name, Look.user_id == create_look.user_id, Look.is_active
        ).first()

        if db_look:
            raise DuplicateError("Look already exists with that name.")

    def __store_look_image_to_s3(self, create_look: CreateLookModel, db_look: Look) -> str:
        timestamp = str(int(time.time() * 1000))
        local_file = f"{TMP_DIR}/{timestamp}.png"
        s3_file = f"looks/{create_look.user_id}/{db_look.id}/{timestamp}.png"

        self.__save_image(create_look.image, local_file)
        self.aws_service.upload_to_s3(local_file, DATA_BUCKET, s3_file)

        return s3_file

    def __get_suit_parts(self, suit_variant_id: str) -> List[ShopifyVariantModel]:
        suit_variants: List[ShopifyVariantModel] = self.shopify_service.get_variants_by_id([suit_variant_id])

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

    def __enrich_product_specs_variants_with_suit_parts(
        self, suit_variant_id: str, product_spec_variants: List[str], suit_parts_variants: List[ShopifyVariantModel]
    ) -> List[str]:
        enriched_product_specs_variants = product_spec_variants.copy()
        enriched_product_specs_variants.remove(suit_variant_id)

        enriched_product_specs_variants = [
            variant.variant_id for variant in suit_parts_variants
        ] + enriched_product_specs_variants

        return enriched_product_specs_variants

    def __convert_sku_spec_to_variant_model(self, create_look: CreateLookModel):
        create_look.product_specs["suit_variant"] = self.shopify_service.get_variant_by_sku(
            create_look.product_specs["suit_variant"]
        ).variant_id

        variants = [create_look.product_specs["suit_variant"]]

        for sku in create_look.product_specs.get("variants", []):
            variants.append(self.shopify_service.get_variant_by_sku(sku).variant_id)

        create_look.product_specs["variants"] = variants

    def create_look(self, create_look: CreateLookModel) -> LookModel:
        self.__verify_that_look_does_not_exist(create_look)

        try:
            if create_look.spec_type == ProductSpecType.SKU:
                self.__convert_sku_spec_to_variant_model(create_look)

            db_look = self.__persist_new_look_to_db(create_look)
            s3_file = self.__store_look_image_to_s3(create_look, db_look) if create_look.image else None

            suit_variant_id = create_look.product_specs.get("suit_variant")

            if not suit_variant_id:
                raise ServiceError("Suit variant id is missing.")

            bundle_id = str(random.randint(100000, 1000000000))

            bundle_identifier_variant_id = str(self.shopify_service.create_bundle_identifier_product(bundle_id))

            enriched_look_variants = create_look.product_specs.get("variants") + [bundle_identifier_variant_id]

            look_variants = self.shopify_service.get_variants_by_id(enriched_look_variants)

            suit_parts_variants = self.__get_suit_parts(suit_variant_id)

            all_variants = look_variants + suit_parts_variants

            id_to_variants = {variant.variant_id: variant for variant in all_variants}

            enriched_product_specs_variants = self.__enrich_product_specs_variants_with_suit_parts(
                suit_variant_id,
                enriched_look_variants,
                suit_parts_variants,
            )

            bundle_product_variant_id = self.shopify_service.create_bundle(
                bundle_id,
                enriched_product_specs_variants,
                image_src=(f"https://{FlaskApp.current().images_data_endpoint_host}/{s3_file}" if s3_file else None),
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
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to create look.", e)

        return LookModel.model_validate(db_look)

    def update_look(self, look_id: uuid.UUID, update_look: UpdateLookModel) -> LookModel:
        db_look = Look.query.filter(Look.id == look_id).first()

        if not db_look:
            raise NotFoundError("Look not found")

        existing_look = Look.query.filter(
            Look.name == update_look.name, Look.user_id == db_look.user_id, Look.id != look_id
        ).first()

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
        look = Look.query.filter(Look.id == look_id).first()

        if not look:
            raise NotFoundError("Look not found")

        num_attendees = Attendee.query.filter(Attendee.look_id == look_id, Attendee.is_active).count()

        if num_attendees > 0:
            raise BadRequestError("Can't delete look associated with attendee")

        try:
            look.is_active = False
            look.updated_at = datetime.now()

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete look.", e)

    def __save_image(self, image_b64: str, local_file: str) -> None:
        try:
            image_b64 = image_b64.replace("data:image/png;base64,", "")
            decoded_image = base64.b64decode(image_b64)

            with open(local_file, "wb") as f:
                f.write(decoded_image)
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to save image.", e)

    def find_look_by_product_id(self, product_id: str) -> Optional[LookModel]:
        query = text(
            f"""
            SELECT id, name, user_id, product_specs, image_path, is_active
            FROM looks 
            WHERE product_specs->'items' IS NOT NULL 
              AND json_typeof(product_specs->'items') = 'array' 
              AND EXISTS (
                SELECT 1 
                FROM json_array_elements(product_specs->'items') AS item 
                WHERE item->>'product_id' = '{product_id}');
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
