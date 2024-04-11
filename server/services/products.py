import uuid

from server.database.models import ProductItem
from server.services import ServiceError, DuplicateError, NotFoundError


class ProductService:
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

    def create_product(self, **kwargs):
        with self.session_factory() as db:
            product = db.query(ProductItem).filter_by(name=kwargs["name"]).first()

            if product:
                raise DuplicateError("Product already exists")

            try:
                product = ProductItem(
                    id=uuid.uuid4(),
                    is_active=kwargs.get("Active", True),
                    name=kwargs["name"],
                    sku=kwargs["SKU"],
                    weight_lb=kwargs["Weight"],
                    height_in=kwargs["Height"],
                    width_in=kwargs["Width"],
                    length_in=kwargs["Length"],
                    value=kwargs["Value"],
                    price=kwargs["Price"],
                    on_hand=kwargs["On_hand"],
                    allocated=kwargs["Allocated"],
                    reserve=kwargs["Reserve"],
                    non_sellable_total=kwargs["Non_sellable_total"],
                    reorder_level=kwargs["Reorder_level"],
                    reorder_amount=kwargs["Reorder_amount"],
                    replenishment_level=kwargs["Replenishment_level"],
                    available=kwargs["Available"],
                    backorder=kwargs["Backorder"],
                    barcode=kwargs["Barcode"],
                    tags=kwargs["Tags"],
                )

                db.add(product)
                db.commit()
                db.refresh(product)
            except Exception as e:
                raise ServiceError("Failed to create product.", e)

        return product

    def update_product(self, product_id, **kwargs):
        with self.session_factory() as db:
            product = db.query(ProductItem).filter_by(id=product_id).first()

            if not product:
                raise NotFoundError()

            try:
                product.name = kwargs["name"]
                product.sku = kwargs["SKU"]
                product.weight_lb = kwargs["Weight"]
                product.height_in = kwargs["Height"]
                product.width_in = kwargs["Width"]
                product.length_in = kwargs["Length"]
                product.value = kwargs["Value"]
                product.price = kwargs["Price"]
                product.on_hand = kwargs["On_hand"]
                product.allocated = kwargs["Allocated"]
                product.reserve = kwargs["Reserve"]
                product.non_sellable_total = kwargs["Non_sellable_total"]
                product.reorder_level = kwargs["Reorder_level"]
                product.reorder_amount = kwargs["Reorder_amount"]
                product.replenishment_level = kwargs["Replenishment_level"]
                product.available = kwargs["Available"]
                product.backorder = kwargs["Backorder"]
                product.barcode = kwargs["Barcode"]
                product.tags = kwargs["Tags"]

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
