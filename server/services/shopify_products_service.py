import logging
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from server.database.database_manager import db
from server.database.models import ShopifyProduct
from server.services import NotFoundError

logger = logging.getLogger(__name__)


class ShopifyProductService:
    @staticmethod
    def get_product_by_id(product_id: int) -> ShopifyProduct:
        product = db.session.execute(
            select(ShopifyProduct).where(ShopifyProduct.product_id == product_id)
        ).scalar_one_or_none()

        if not product:
            raise NotFoundError(f"Product with product_id: {product_id} not found")

        return product

    @staticmethod
    def get_variant_by_id(variant_id: int) -> ShopifyProduct:
        product = db.session.execute(
            select(ShopifyProduct).where(ShopifyProduct.data["variants"].contains([{"id": variant_id}]))
        ).scalar_one_or_none()

        if not product:
            raise NotFoundError(f"Product with variant_id: {variant_id} not found")

        return product

    @staticmethod
    def get_variant_by_sku(variant_sku: str) -> ShopifyProduct:
        product = db.session.execute(
            select(ShopifyProduct).where(ShopifyProduct.data["variants"].contains([{"sku": variant_sku}]))
        ).scalar_one_or_none()

        if not product:
            raise NotFoundError(f"Product with variant_sku: {variant_sku} not found")

        return product

    @staticmethod
    def upsert_product(product_id: int, data: dict[str, Any]) -> ShopifyProduct | None:
        try:
            stmt = (
                insert(ShopifyProduct)
                .values(product_id=product_id, data=data, is_deleted=False)
                .on_conflict_do_update(
                    index_elements=["product_id"],
                    set_={
                        "data": data,
                        "updated_at": text("now()"),
                        "is_deleted": False,
                    },
                )
            )

            db.session.execute(stmt)
            db.session.commit()

            upserted_product = db.session.execute(
                select(ShopifyProduct).where(ShopifyProduct.product_id == product_id)
            ).scalar_one_or_none()

            return upserted_product
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception(f"Failed to upsert product with product_id: {product_id}", e)
            return None

    @staticmethod
    def delete_product(product_id: int) -> ShopifyProduct | None:
        product = db.session.execute(
            select(ShopifyProduct).where(ShopifyProduct.product_id == product_id)
        ).scalar_one_or_none()

        if not product:
            logger.warning(f"Product with product_id: {product_id} not found")
            return

        try:
            product.is_deleted = True
            product.updated_at = text("now()")

            db.session.commit()
            db.session.refresh(product)
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Failed to mark product as deleted: {product_id}", e)

        return product
