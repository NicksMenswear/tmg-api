import logging
from enum import Enum
from typing import Optional

from server.models.measurement_model import MeasurementModel
from server.models.size_model import SizeModel
from server.services import ServiceError

SIZE_CODES = {
    "34": "34",
    "36": "36",
    "38": "38",
    "40": "40",
    "42": "42",
    "44": "44",
    "46": "46",
    "48": "48",
    "50": "50",
    "52": "52",
    "54": "54",
    "56": "56",
    "58": "58",
    "60": "60",
    "62": "62",
    "64": "64",
    "14": "140",
    "14.5": "145",
    "14 1/2": "145",
    "141/2": "145",
    "15": "150",
    "15.5": "155",
    "15 1/2": "155",
    "151/2": "155",
    "16": "160",
    "16.5": "165",
    "16 1/2": "165",
    "161/2": "165",
    "17": "170",
    "17.5": "175",
    "17 1/2": "175",
    "171/2": "175",
    "18": "180",
    "18.5": "185",
    "18 1/2": "185",
    "181/2": "185",
    "19": "190",
    "19.5": "195",
    "19 1/2": "195",
    "191/2": "195",
    "20": "200",
    "21": "210",
    "22": "220",
    "23": "230",
}

VEST_SIZE_CODES = {
    "34": "2XS",
    "36": "0XS",
    "38": "00S",
    "40": "00M",
    "42": "00L",
    "44": "0XL",
    "46": "02X",
    "48": "03X",
    "50": "04X",
    "52": "05X",
    "54": "05X",
    "56": "06X",
    "58": "06X",
    "60": "06X",
    "62": "06X",
    "64": "06X",
}

LENGTH_CODES = {
    "S": "S",
    "R": "R",
    "L": "L",
    "XL": "X",
    "X": "X",
    "30/31": "1",
    "32/33": "3",
    "33": "3",
    "32": "3",
    "34/35": "5",
    "35": "5",
    "34": "5",
    "36/37": "7",
    "36": "7",
    "37": "7",
    "38/39": "9",
    "OSR": "OSR",
}

SHOES_SIZE_CODES = {
    "7": "070D",
    "7 Wide": "070W",
    "7.5": "075D",
    "7.5 Wide": "075W",
    "8": "080D",
    "8 Wide": "080W",
    "8.5": "085D",
    "8.5 Wide": "085W",
    "9": "090D",
    "9 Wide": "090W",
    "9.5": "095D",
    "9.5 Wide": "095W",
    "10": "100D",
    "10 Wide": "100W",
    "10.5": "105D",
    "10.5 Wide": "105W",
    "11": "110D",
    "11 Wide": "110W",
    "11.5": "115D",
    "11.5 Wide": "115W",
    "12": "120D",
    "12 Wide": "120W",
    "13": "130D",
    "13 Wide": "130W",
    "14": "140D",
    "14 Wide": "140W",
    "15": "150D",
    "15 Wide": "150W",
    "16": "160D",
    "16 Wide": "160W",
}


class ProductType(Enum):
    SUIT = "0"
    JACKET = "1"
    PANTS = "2"  # partially
    VEST = "3"
    SHIRT = "4"
    BOW_TIE = "5"
    NECK_TIE = "6"
    BELT = "7"
    SHOES = "8"
    SOCKS = "9"
    THREE_PIECE_SUIT_OR_TUX = "0"
    SWATCHES = "S"


logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class SkuBuilder:
    def build(self, shopify_sku: str, size_model: SizeModel, measurement_model: MeasurementModel) -> Optional[str]:
        if not shopify_sku or not size_model or not measurement_model:
            raise ServiceError("Missing required data")

        product_type = self.__get_product_type_by_sku(shopify_sku)

        if product_type == ProductType.JACKET:
            return self.__build_jacket_sku(shopify_sku, size_model)
        elif product_type == ProductType.PANTS:
            return self.__build_pants_sku(shopify_sku, size_model)
        elif product_type == ProductType.VEST:
            return self.__build_vest_sku(shopify_sku, size_model)
        elif product_type == ProductType.SHIRT:
            return self.__build_shirt_sku(shopify_sku, size_model)
        elif product_type == ProductType.NECK_TIE:
            return self.__build_neck_tie_sku(shopify_sku)
        elif product_type == ProductType.BOW_TIE:
            return self.__build_bow_tie_sku(shopify_sku)
        elif product_type == ProductType.BELT:
            return self.__build_belt_sku(shopify_sku, size_model)
        elif product_type == ProductType.SHOES:
            return self.__build_shoes_sku(shopify_sku, measurement_model)
        elif product_type == ProductType.SOCKS:
            return self.__build_socks_sku(shopify_sku)
        elif product_type == ProductType.SOCKS:
            return self.__build_socks_sku(shopify_sku)
        else:
            raise ServiceError("Unsupported product type")

    def __get_product_type_by_sku(self, sku: str) -> ProductType:
        prefix = sku[0]

        for product_type in ProductType:
            if product_type.value == prefix:
                return product_type

        raise ServiceError(f"Unsupported SKU type: {sku}")

    def __build_jacket_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        jacket_size = SIZE_CODES.get(size_model.jacket_size)

        if not jacket_size:
            raise ServiceError(f"Unsupported jacket size: {size_model.jacket_size}")

        return f"{shopify_sku}{jacket_size}R"

    def __build_pants_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        return f"{shopify_sku}{size_model.pant_size}R"

    def __build_vest_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        vest_size_code = VEST_SIZE_CODES.get(size_model.vest_size)

        if not vest_size_code:
            raise ServiceError(f"Unsupported vest size: {size_model.vest_size}")

        return f"{shopify_sku}{vest_size_code}"

    def __build_shirt_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        shirt_neck_size = SIZE_CODES.get(size_model.shirt_neck_size)
        shirt_length_code = LENGTH_CODES.get(size_model.shirt_sleeve_length)

        if not shirt_neck_size:
            raise ServiceError(f"Unsupported shirt neck size: {size_model.shirt_neck_size}")

        if not shirt_length_code:
            raise ServiceError(f"Unsupported shirt sleeve length: {size_model.shirt_sleeve_length}")

        return f"{shopify_sku}{shirt_neck_size}{shirt_length_code}"

    def __build_neck_tie_sku(self, shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"

    def __build_bow_tie_sku(self, shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"

    def __build_belt_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        try:
            pant_size_num = int(size_model.pant_size)
        except ValueError:
            raise ServiceError(f"Unsupported pant size: {size_model.pant_size}")

        if 28 <= pant_size_num <= 46:
            pant_size = "46"
        elif 48 <= pant_size_num <= 60:
            pant_size = "60"
        else:
            raise ServiceError(f"Unsupported pant size: {size_model.pant_size}")

        return f"{shopify_sku}{pant_size}A"

    def __build_shoes_sku(self, shopify_sku: str, measurement_model: MeasurementModel) -> str:
        shoe_size = SHOES_SIZE_CODES.get(measurement_model.shoe_size)

        if not shoe_size:
            raise ServiceError(f"Unsupported shoe size: {measurement_model.shoe_size}")

        return f"{shopify_sku}{shoe_size}"

    def __build_socks_sku(self, shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"
