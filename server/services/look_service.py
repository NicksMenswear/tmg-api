import base64
import logging
import os
import time
import uuid
from datetime import datetime
from typing import List

from server.database.database_manager import db
from server.database.models import Look, Attendee
from server.flask_app import FlaskApp
from server.models.look_model import CreateLookModel, LookModel, UpdateLookModel
from server.models.shopify_model import ShopifyVariantModel
from server.services import ServiceError, DuplicateError, NotFoundError, BadRequestError
from server.services.aws_service import AbstractAWSService
from server.services.shopify_service import AbstractShopifyService
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

        return LookModel.from_orm(db_look)

    def get_looks_by_user_id(self, user_id: uuid.UUID) -> List[LookModel]:
        look_models = [
            LookModel.from_orm(look)
            for look in Look.query.filter(Look.user_id == user_id, Look.is_active).order_by(Look.created_at.asc()).all()
        ]

        bundle_variants = set()

        for look_model in look_models:
            bundle_variant_id = look_model.product_specs.get("bundle", {}).get("variant_id")

            if bundle_variant_id:
                bundle_variants.add(bundle_variant_id)

        if bundle_variants:
            bundle_variants_with_prices = self.shopify_service.get_variant_prices(list(bundle_variants))

            for look_model in look_models:
                bundle_variant_id = look_model.product_specs.get("bundle", {}).get("variant_id")
                look_model.price = bundle_variants_with_prices.get(bundle_variant_id, 0.0) if bundle_variant_id else 0.0

        return look_models

    def get_look_price(self, look) -> float:
        bundle_variant_id = look.product_specs.get("bundle", {}).get("variant_id")

        if not bundle_variant_id:
            return 0.0

        return self.shopify_service.get_variant_prices([bundle_variant_id])[bundle_variant_id]

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
        db.session.commit()
        db.session.refresh(look)

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
            raise ServiceError("Invalid suit variant sku.")

        jacket_sku = "1" + suit_sku[1:]
        pants_sku = "2" + suit_sku[1:]
        vest_sku = "3" + suit_sku[1:]

        jacket_variant = self.shopify_service.get_variant_by_sku(jacket_sku)
        pants_variant = self.shopify_service.get_variant_by_sku(pants_sku)
        vest_variant = self.shopify_service.get_variant_by_sku(vest_sku)

        if not jacket_variant or not pants_variant or not vest_variant:
            raise ServiceError("Not all suit parts were found.")

        return [jacket_variant, pants_variant, vest_variant]

    def __enrich_product_specs_variants_with_suit_parts(
        self, suit_variant_id: str, product_specs: dict, suit_parts_variants: List[ShopifyVariantModel]
    ) -> List[str]:
        enriched_product_specs_variants = product_specs.get("variants").copy()
        enriched_product_specs_variants.remove(suit_variant_id)

        enriched_product_specs_variants = [
            variant.variant_id for variant in suit_parts_variants
        ] + enriched_product_specs_variants

        return enriched_product_specs_variants

    def create_look(self, create_look: CreateLookModel) -> LookModel:
        self.__verify_that_look_does_not_exist(create_look)

        try:
            db_look = self.__persist_new_look_to_db(create_look)
            s3_file = self.__store_look_image_to_s3(create_look, db_look) if create_look.image else None

            suit_variant_sku = create_look.product_specs.get("suit_variant_sku")  # used for testing only
            suit_variant_id = create_look.product_specs.get("suit_variant")

            if suit_variant_sku and not suit_variant_id:  # used for testing only
                suit_variant = self.shopify_service.get_variant_by_sku(suit_variant_sku)
                suit_variant_id = suit_variant.variant_id if suit_variant else None
                create_look.product_specs["suit_variant"] = suit_variant_id

            if not suit_variant_id:
                raise ServiceError("Suit variant id is missing.")

            look_variants = self.shopify_service.get_variants_by_id(create_look.product_specs.get("variants"))
            suit_parts_variants = self.__get_suit_parts(suit_variant_id)

            all_variants = look_variants + suit_parts_variants
            id_to_variants = {variant.variant_id: variant for variant in all_variants}

            enriched_product_specs_variants = self.__enrich_product_specs_variants_with_suit_parts(
                suit_variant_id,
                create_look.product_specs,
                suit_parts_variants,
            )

            bundle_product_variant_id = self.shopify_service.create_bundle(
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

        return LookModel.from_orm(db_look)

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

        return LookModel.from_orm(db_look)

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
