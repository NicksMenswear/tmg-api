import base64
import logging
import os
import uuid
from datetime import datetime
from typing import List

import time

from server.database.database_manager import db
from server.database.models import Look, Attendee
from server.flask_app import FlaskApp
from server.models.look_model import CreateLookModel, LookModel, UpdateLookModel
from server.services import ServiceError, DuplicateError, NotFoundError, BadRequestError
from server.services.aws import AbstractAWSService
from server.services.shopify import AbstractShopifyService
from server.services.user import UserService

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

    def create_look(self, create_look: CreateLookModel) -> LookModel:
        db_look: Look = Look.query.filter(
            Look.name == create_look.name, Look.user_id == create_look.user_id, Look.is_active
        ).first()

        if db_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            db_look = Look(
                id=uuid.uuid4(),
                name=create_look.name,
                user_id=create_look.user_id,
                product_specs=create_look.product_specs,
                image_path=None,
                is_active=create_look.is_active,
            )

            db.session.add(db_look)
            db.session.commit()
            db.session.refresh(db_look)

            s3_file = None

            if create_look.image:
                timestamp = str(int(time.time() * 1000))
                local_file = f"{TMP_DIR}/{timestamp}.png"
                s3_file = f"looks/{create_look.user_id}/{db_look.id}/{timestamp}.png"

                self.__save_image(create_look.image, local_file)
                self.aws_service.upload_to_s3(local_file, DATA_BUCKET, s3_file)

            bundle_product_variant_id = self.shopify_service.create_bundle(
                create_look.product_specs.get("variants"),
                image_src=(f"https://{FlaskApp.current().images_data_endpoint_host}/{s3_file}" if s3_file else None),
            )

            if not bundle_product_variant_id:
                raise ServiceError("Failed to create bundle product variant.")

            variant_ids_with_titles = self.shopify_service.get_variant_product_title(
                create_look.product_specs.get("variants")
            )

            enriched_product_specs = {
                "bundle": {"variant_id": bundle_product_variant_id},
                "items": variant_ids_with_titles,
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
