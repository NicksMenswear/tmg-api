import logging

from flask import jsonify

from server.services import ServiceError, NotFoundError, DuplicateError
from server.services.product import ProductService

logger = logging.getLogger(__name__)


def create_product_item(product_item):
    product_service = ProductService()

    try:
        product = product_service.create_product(product_item)
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": DuplicateError.MESSAGE}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create product"}), 500

    return product.to_dict(), 201


def list_product_items():
    product_service = ProductService()

    products = product_service.get_all_active_products()

    return [product.to_dict() for product in products], 200


def single_product_item(product_id):
    product_service = ProductService()

    product = product_service.get_active_product_by_id(product_id)

    if not product:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return product.to_dict(), 200


def update_product_item(product_data):
    product_service = ProductService()

    try:
        product = product_service.update_product(product_data["id"], product_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to update product."}), 500

    return product.to_dict(), 200


def soft_delete_product(product_data):
    product_service = ProductService()

    try:
        product_service.deactivate_product(product_data["id"])
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to deactivate product."}), 500

    return None, 204
