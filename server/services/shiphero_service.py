import json
import logging
import os
import uuid
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.models.shiphero_model import ShipHeroProductModel
from server.services import ServiceError

logger = logging.getLogger(__name__)


class AbstractShipHeroService(ABC):
    @abstractmethod
    def get_product_by_sku(self, sku: str) -> ShipHeroProductModel:
        pass


class FakeShipHeroService(AbstractShipHeroService):
    def get_product_by_sku(self, sku: str) -> ShipHeroProductModel:
        return ShipHeroProductModel(
            id=f"{uuid.uuid4()}",
            name=f"Fake Product {uuid.uuid4()}",
            sku=sku,
        )


class ShipHeroService(AbstractShipHeroService):
    def __init__(self):
        self.__shiphero_api_url = os.getenv("SHIPHERO_API_URL", "https://public-api.shiphero.com/")
        self.__shiphero_api_graphql_endpoint = f"{self.__shiphero_api_url}/graphql"
        self.__shiphero_api_access_token = os.getenv("SHIPHERO_API_ACCESS_TOKEN")

    def api_request(self, method, endpoint, body=None) -> tuple[int, dict]:
        response = http(
            method,
            endpoint,
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.__shiphero_api_access_token}",
            },
        )

        return response.status, json.loads(response.data.decode("utf-8"))

    def get_product_by_sku(self, sku: str) -> ShipHeroProductModel:
        status, response = self.api_request(
            "POST",
            self.__shiphero_api_graphql_endpoint,
            {
                "query": f"""
                    query {{
                        product(sku: "{sku}") {{
                            request_id
                            complexity
                            data {{
                                id
                                name
                                sku
                                price
                            }}
                        }}
                    }}
                """
            },
        )

        if status != 200:
            logger.error(f"Failed to get product by SKU {sku}: {response}")
            raise ServiceError(f"Failed to get product by SKU {sku}")

        if "errors" in response:
            logger.error(f"Failed to get product by SKU {sku}: {response['errors']}")
            raise ServiceError(f"Failed to get product by SKU {sku}")

        product = response.get("data", {}).get("product", {}).get("data")

        if not product:
            logger.error(f"Invalid response from shiphero for SKU {sku}: {response}")
            raise ServiceError(f"Invalid response from shiphero for SKU {sku}")

        return ShipHeroProductModel(**product)


if __name__ == "__main__":
    service = ShipHeroService()
    print(service.get_product_by_sku("101A2BLK38SAF"))
