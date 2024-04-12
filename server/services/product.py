import uuid

from server.database.models import ProductItem
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.base import BaseService


class ProductService(BaseService):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_product_by_name(self, name):
        with self.session_factory() as db:
            return db.query(ProductItem).filter_by(name=name).first()

    def get_product_by_id(self, product_id):
        with self.session_factory() as db:
            return db.query(ProductItem).filter_by(id=product_id).first()

    def get_active_product_by_id(self, product_id):
        with self.session_factory() as db:
            return db.query(ProductItem).filter_by(id=product_id, is_active=True).first()

    def get_all_active_products(self):
        with self.session_factory() as db:
            return db.query(ProductItem).filter_by(is_active=True).all()

    def create_product(self, **product_data):
        with self.session_factory() as db:
            product = db.query(ProductItem).filter_by(name=product_data["name"]).first()

            if product:
                raise DuplicateError("Product already exists")

            try:
                product = ProductItem(
                    id=uuid.uuid4(),
                    is_active=product_data.get("Active", True),
                    name=product_data["name"],
                    sku=product_data["SKU"],
                    weight_lb=product_data["Weight"],
                    height_in=product_data["Height"],
                    width_in=product_data["Width"],
                    length_in=product_data["Length"],
                    value=product_data["Value"],
                    price=product_data["Price"],
                    on_hand=product_data["On_hand"],
                    allocated=product_data["Allocated"],
                    reserve=product_data["Reserve"],
                    non_sellable_total=product_data["Non_sellable_total"],
                    reorder_level=product_data["Reorder_level"],
                    reorder_amount=product_data["Reorder_amount"],
                    replenishment_level=product_data["Replenishment_level"],
                    available=product_data["Available"],
                    backorder=product_data["Backorder"],
                    barcode=product_data["Barcode"],
                    tags=product_data["Tags"],
                )

                db.add(product)
                db.commit()
                db.refresh(product)
            except Exception as e:
                raise ServiceError("Failed to create product.", e)

        return product

    def update_product(self, product_id, **product_data):
        with self.session_factory() as db:
            product = db.query(ProductItem).filter_by(id=product_id).first()

            if not product:
                raise NotFoundError()

            try:
                product.name = product_data["name"]
                product.sku = product_data["SKU"]
                product.weight_lb = product_data["Weight"]
                product.height_in = product_data["Height"]
                product.width_in = product_data["Width"]
                product.length_in = product_data["Length"]
                product.value = product_data["Value"]
                product.price = product_data["Price"]
                product.on_hand = product_data["On_hand"]
                product.allocated = product_data["Allocated"]
                product.reserve = product_data["Reserve"]
                product.non_sellable_total = product_data["Non_sellable_total"]
                product.reorder_level = product_data["Reorder_level"]
                product.reorder_amount = product_data["Reorder_amount"]
                product.replenishment_level = product_data["Replenishment_level"]
                product.available = product_data["Available"]
                product.backorder = product_data["Backorder"]
                product.barcode = product_data["Barcode"]
                product.tags = product_data["Tags"]

                db.commit()
                db.refresh(product)
            except Exception as e:
                raise ServiceError("Failed to update product.", e)

            return product

    def deactivate_product(self, product_id):
        with self.session_factory() as db:
            product = db.query(ProductItem).filter_by(id=product_id).first()

            if not product:
                raise NotFoundError()

            product.is_active = False

            try:
                db.commit()
                db.refresh(product)
            except Exception as e:
                raise ServiceError("Failed to deactivate product.", e)

            return product
