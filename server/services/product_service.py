import logging
import uuid
from typing import List

from sqlalchemy import func

from server.database.database_manager import db
from server.database.models import Product, OrderItem
from server.models.order_model import ProductModel
from server.services import NotFoundError, ServiceError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ProductService:
    def __init__(self):
        pass

    def get_num_products(self) -> int:
        return Product.query.count()

    def get_product_by_id(self, product_id: uuid.UUID) -> ProductModel:
        product = Product.query.filter(Product.id == product_id).first()

        if not product:
            raise NotFoundError("Product not found")

        return ProductModel.from_orm(product)

    def get_product_by_sku(self, sku: str) -> ProductModel:
        product = Product.query.filter(
            Product.sku == sku, Product.shopify_sku.is_(None), func.length(Product.sku) > 8
        ).first()

        if not product:
            raise NotFoundError("Product not found")

        return ProductModel.from_orm(product)

    def get_products_for_order(self, order_id: uuid.UUID) -> List[ProductModel]:
        return [
            ProductModel.from_orm(product)
            for product in Product.query.join(OrderItem).filter(OrderItem.order_id == order_id).all()
        ]

    def update_sku_for_product(self, product_id: uuid.UUID, sku: str) -> ProductModel:
        try:
            product = Product.query.filter(Product.id == product_id).first()
            product.sku = sku

            db.session.commit()
            db.session.refresh(product)
        except Exception as e:
            raise ServiceError("Failed to update SKU for product.", e)

        return ProductModel.from_orm(product)
