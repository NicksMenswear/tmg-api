import base64
import logging
import os
import tempfile
from typing import Any

import requests

from server.database.database_manager import db
from server.database.models import SuitBuilderItem, SuitBuilderItemType
from server.models.shopify_model import ShopifyVariantModel
from server.models.suit_builder_model import (
    CreateSuitBuilderModel,
    SuitBuilderItemModel,
    SuitBuilderItemsCollection,
)
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.integrations.aws_service import AbstractAWSService
from server.services.integrations.shopify_service import AbstractShopifyService

DATA_BUCKET = os.environ.get("DATA_BUCKET", "data-bucket")

logger = logging.getLogger(__name__)


class SuitBuilderService:
    def __init__(self, shopify_service: AbstractShopifyService, aws_service: AbstractAWSService):
        self.shopify_service: AbstractShopifyService = shopify_service
        self.aws_service: AbstractAWSService = aws_service

    @staticmethod
    def __build_image_path(item_type: str, sku: str) -> str:
        return f"suit-builder/v1/{item_type}/{sku}.png"

    @staticmethod
    def __build_icon_path(item_type: str, sku: str) -> str:
        return f"suit-builder/v1/{item_type}/{sku}-icon.png"

    def add_item(self, item: CreateSuitBuilderModel) -> SuitBuilderItemModel:
        suit_builder_item = SuitBuilderItem.query.filter(SuitBuilderItem.sku == item.sku).first()

        if suit_builder_item:
            raise DuplicateError(f"Item with sku {item.sku} already exists")

        try:
            shopify_variant: ShopifyVariantModel = self.shopify_service.get_variant_by_sku(item.sku)
        except ServiceError as e:
            raise ServiceError(f"Failed to fetch item from Shopify: {e}")

        try:
            suit_builder_item: SuitBuilderItem = SuitBuilderItem(
                type=SuitBuilderItemType(item.type),
                sku=item.sku,
                name=shopify_variant.product_title,
                variant_id=shopify_variant.variant_id,
                product_id=shopify_variant.product_id,
                price=shopify_variant.variant_price,
            )

            if shopify_variant.image_url:
                response = requests.get(shopify_variant.image_url)

                if response.status_code == 200:
                    image_path = os.path.join(tempfile.gettempdir(), f"{suit_builder_item.sku}.png")

                    with open(image_path, "wb") as f:
                        f.write(response.content)

                    self.aws_service.upload_to_s3(
                        image_path,
                        DATA_BUCKET,
                        self.__build_image_path(suit_builder_item.type.value, suit_builder_item.sku),
                    )
                    self.aws_service.upload_to_s3(
                        image_path,
                        DATA_BUCKET,
                        self.__build_icon_path(suit_builder_item.type.value, suit_builder_item.sku),
                    )

            db.session.add(suit_builder_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to add suit builder item", e)

        return SuitBuilderItemModel.from_orm(suit_builder_item)

    def get_items(self, enriched: bool = False) -> SuitBuilderItemsCollection:
        query = SuitBuilderItem.query

        if not enriched:
            query = query.filter(SuitBuilderItem.is_active)

        suit_builder_items = query.all()

        grouped_collections = SuitBuilderItemsCollection()

        for item in suit_builder_items:
            grouped_collections.add_item(SuitBuilderItemModel.from_orm(item))

        return grouped_collections

    def patch_item(self, sku: str, field: str, value: Any) -> SuitBuilderItemModel:
        suit_builder_item = SuitBuilderItem.query.filter(SuitBuilderItem.sku == sku).first()

        if not suit_builder_item:
            raise NotFoundError(f"Item with sku {sku} not found")

        if field == "is_active":
            suit_builder_item.is_active = bool(value)
        elif field == "index":
            suit_builder_item.index = int(value)
        elif field == "image_b64":
            local_file_path = f"{tempfile.gettempdir()}/{suit_builder_item.sku}.png"
            self.__save_image(value, local_file_path)
            self.aws_service.upload_to_s3(
                local_file_path,
                DATA_BUCKET,
                self.__build_image_path(suit_builder_item.type.value, suit_builder_item.sku),
            )
        elif field == "icon_b64":
            local_file_path = f"{tempfile.gettempdir()}/{suit_builder_item.sku}-icon.png"
            self.__save_image(value, local_file_path)
            self.aws_service.upload_to_s3(
                local_file_path,
                DATA_BUCKET,
                self.__build_icon_path(suit_builder_item.type.value, suit_builder_item.sku),
            )
        else:
            raise ServiceError(f"Field {field} not supported")

        try:
            db.session.commit()
            db.session.refresh(suit_builder_item)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to patch suit builder item", e)

        return SuitBuilderItemModel.from_orm(suit_builder_item)

    def delete_item(self, sku: str) -> None:
        suit_builder_item = SuitBuilderItem.query.filter(SuitBuilderItem.sku == sku).first()

        if not suit_builder_item:
            raise NotFoundError(f"Item with sku {sku} not found")

        try:
            self.aws_service.delete_from_s3(
                DATA_BUCKET, self.__build_image_path(suit_builder_item.type.value, suit_builder_item.sku)
            )
            self.aws_service.delete_from_s3(
                DATA_BUCKET, self.__build_icon_path(suit_builder_item.type.value, suit_builder_item.sku)
            )
        except Exception as e:
            logger.warning(f"Failed to delete from S3: {e}. This is fine.")

        try:
            db.session.delete(suit_builder_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to delete suit builder item", e)

    @staticmethod
    def __save_image(image_b64: str, local_file: str) -> None:
        try:
            decoded_image = base64.b64decode(image_b64)

            with open(local_file, "wb") as f:
                f.write(decoded_image)
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to save image.", e)
