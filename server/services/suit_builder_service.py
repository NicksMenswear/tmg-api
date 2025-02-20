import base64
import logging
import os
import tempfile
from datetime import datetime
from typing import Any

import requests
from sqlalchemy import select

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
from server.services.shopify_product_service import ShopifyProductService

DATA_BUCKET = os.environ.get("DATA_BUCKET", "data-bucket")

logger = logging.getLogger(__name__)


class SuitBuilderService:
    def __init__(
        self,
        shopify_service: AbstractShopifyService,
        aws_service: AbstractAWSService,
        shopify_product_service: ShopifyProductService,
    ):
        self.shopify_service: AbstractShopifyService = shopify_service
        self.aws_service: AbstractAWSService = aws_service
        self.shopify_product_service = shopify_product_service

    @staticmethod
    def __build_s3_image_path(item_type: str, filename: str) -> str:
        return f"suit-builder/v1/{item_type}/{filename}"

    def __save_image_by_url_to_s3(self, url: str, image_type: str, filename: str) -> None:
        image_path = os.path.join(tempfile.gettempdir(), filename)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(response.content)
        else:
            raise ServiceError(f"Failed to download image from {url}")

        self.aws_service.upload_to_s3(
            image_path,
            DATA_BUCKET,
            self.__build_s3_image_path(image_type, filename),
        )

    def add_item(self, item: CreateSuitBuilderModel) -> SuitBuilderItemModel:
        suit_builder_item = db.session.execute(
            select(SuitBuilderItem).where(SuitBuilderItem.sku == item.sku)
        ).scalar_one_or_none()

        if suit_builder_item:
            raise DuplicateError(f"Item with sku {item.sku} already exists")

        try:
            shopify_variant: ShopifyVariantModel = self.shopify_product_service.get_product_by_variant_sku(item.sku)
        except ServiceError as e:
            raise ServiceError(f"Failed to fetch item from Shopify: {e}")

        try:
            suit_builder_item: SuitBuilderItem = SuitBuilderItem(
                type=SuitBuilderItemType(item.type),
                sku=item.sku,
                name=shopify_variant.product_title,
                index=item.index,
            )

            if item.image_url:
                self.__save_image_by_url_to_s3(item.image_url, item.type, f"{item.sku}.png")

            if item.icon_url:
                self.__save_image_by_url_to_s3(item.icon_url, item.type, f"{item.sku}-icon.png")

            if not item.image_url and not item.image_url and shopify_variant.image_url:
                self.__save_image_by_url_to_s3(shopify_variant.image_url, item.type, f"{item.sku}.png")
                self.__save_image_by_url_to_s3(shopify_variant.image_url, item.type, f"{item.sku}-icon.png")

            db.session.add(suit_builder_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to add suit builder item", e)

        shopify_product = self.shopify_product_service.get_product_by_variant_sku(suit_builder_item.sku)

        return SuitBuilderItemModel(
            id=suit_builder_item.id,
            type=suit_builder_item.type.value,
            sku=suit_builder_item.sku,
            variant_id=int(shopify_product.variant_id),
            name=suit_builder_item.name,
            index=suit_builder_item.index,
            is_active=suit_builder_item.is_active,
            price=float(shopify_product.variant_price),
        )

    @staticmethod
    def get_items(enriched: bool = False) -> SuitBuilderItemsCollection:
        query = db.text(
            """
            SELECT
                sbi.id,
                sbi.type,
                sbi.sku,
                variant_data.title as name,
                sbi.index,
                sbi.is_active,
                sbi.created_at,
                sbi.updated_at,
                variant->>'id' AS variant_id,
                variant->>'price' AS price,
                variant->>'compare_at_price' AS compare_at_price
            FROM
                suit_builder_items sbi
            JOIN LATERAL
                (
                    SELECT
                        variant,
                        sp.data->>'title' AS title
                    FROM
                        shopify_products sp,
                        jsonb_array_elements(sp.data->'variants') variant
                    WHERE
                        variant->>'sku' = sbi.sku
                ) variant_data ON true
            WHERE
                sbi.is_active = true
            ORDER BY
                sbi.index DESC,
                sbi.sku ASC;
        """
        )

        rows = db.session.execute(query).fetchall()

        grouped_collections = SuitBuilderItemsCollection()

        for row in rows:
            grouped_collections.add_item(
                SuitBuilderItemModel(
                    id=row.id,
                    type=row.type.lower(),
                    sku=row.sku,
                    variant_id=int(row.variant_id),
                    name=row.name,
                    index=row.index,
                    is_active=row.is_active,
                    price=float(row.price),
                    compare_at_price=float(row.compare_at_price) if row.compare_at_price else None,
                )
            )

        return grouped_collections

    def patch_item(self, sku: str, field: str, value: Any) -> SuitBuilderItemModel:
        suit_builder_item = db.session.execute(
            select(SuitBuilderItem).where(SuitBuilderItem.sku == sku)
        ).scalar_one_or_none()

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
                self.__build_s3_image_path(suit_builder_item.type.value, f"{suit_builder_item.sku}.png"),
            )
        elif field == "icon_b64":
            local_file_path = f"{tempfile.gettempdir()}/{suit_builder_item.sku}-icon.png"
            self.__save_image(value, local_file_path)
            self.aws_service.upload_to_s3(
                local_file_path,
                DATA_BUCKET,
                self.__build_s3_image_path(suit_builder_item.type.value, f"{suit_builder_item.sku}-icon.png"),
            )
        else:
            raise ServiceError(f"Field {field} not supported")

        try:
            suit_builder_item.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(suit_builder_item)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to patch suit builder item", e)

        return SuitBuilderItemModel.model_validate(suit_builder_item)

    def delete_item(self, sku: str) -> None:
        suit_builder_item = db.session.execute(
            select(SuitBuilderItem).where(SuitBuilderItem.sku == sku)
        ).scalar_one_or_none()

        if not suit_builder_item:
            raise NotFoundError(f"Item with sku {sku} not found")

        try:
            self.aws_service.delete_from_s3(
                DATA_BUCKET,
                self.__build_s3_image_path(suit_builder_item.type.value, f"{suit_builder_item.sku}.png"),
            )
            self.aws_service.delete_from_s3(
                DATA_BUCKET,
                self.__build_s3_image_path(suit_builder_item.type.value, f"{suit_builder_item.sku}-icon.png"),
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
