import logging
import uuid
from typing import List

from sqlalchemy import func

from server.database.database_manager import db
from server.database.models import Product, OrderItem
from server.models.product_model import CreateProductModel, ProductModel
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

        return ProductModel.model_validate(product)

    def get_product_by_sku(self, sku: str) -> ProductModel:
        product = Product.query.filter(
            Product.sku == sku,
            func.length(Product.sku) > 8,  # this should be removed later once db is fixed
        ).first()

        if not product:
            raise NotFoundError("Product not found")

        return ProductModel.model_validate(product)

    def get_products_for_order(self, order_id: uuid.UUID) -> List[ProductModel]:
        return [
            ProductModel.model_validate(product)
            for product in Product.query.join(OrderItem).filter(OrderItem.order_id == order_id).all()
        ]

    def create_product(self, create_product: CreateProductModel) -> ProductModel:
        try:
            new_product = Product(sku=create_product.sku, name=create_product.name, price=create_product.price)

            db.session.add(new_product)
            db.session.commit()
            db.session.refresh(new_product)
        except Exception as e:
            raise ServiceError("Failed to save new product.", e)

        return ProductModel.model_validate(new_product)
