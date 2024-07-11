import logging
from enum import Enum
from typing import Optional

from server.models.measurement_model import MeasurementModel
from server.models.size_model import SizeModel
from server.services import ServiceError

# jackets
JACKET_SIZES = {"34", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66"}
JACKET_LENGTHS = {"S", "R", "L", "X"}

# vests
VEST_SIZES = {"34", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62", "64"}
VEST_LENGTHS = {"R"}  # set of 1 for now, ¯\_(ツ)_/¯
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

# pants
PANT_SIZES = {"28", "30", "32", "34", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58"}
PANT_LENGTHS = {"R"}  # set of 1 for now, ¯\_(ツ)_/¯

# shirts
SHIRT_NECK_SIZES = {
    "14",
    "14.5",
    "15",
    "15.5",
    "16",
    "16.5",
    "17",
    "17.5",
    "18",
    "18.5",
    "19",
    "19.5",
    "20",
    "21",
    "22",
    "23",
}
SHIRT_NECK_SIZES_MAP = {
    "14": "140",
    "14.5": "145",
    "15": "150",
    "15.5": "155",
    "16": "160",
    "16.5": "165",
    "17": "170",
    "17.5": "175",
    "18": "180",
    "18.5": "185",
    "19": "190",
    "19.5": "195",
    "20": "200",
    "21": "210",
    "22": "220",
    "23": "230",
}
SHIRT_SLEEVE_LENGTHS = {
    "32/33",
    "34/35",
    "36/37",
    "38/39",
}
SHIRT_SLEEVE_LENGTHS_MAP = {
    "32/33": "3",
    "34/35": "5",
    "36/37": "7",
    "38/39": "9",
}

# shoes
SHOES_SIZE_CODES = {
    "7": "070D",
    "7.5": "075D",
    "8": "080D",
    "8.5": "085D",
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
    "16": "160D",
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
    PREMIUM_POCKET_SQUARE = "P"


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
        elif product_type == ProductType.SWATCHES:
            return self.__build_swatches_sku(shopify_sku)
        elif product_type == ProductType.PREMIUM_POCKET_SQUARE:
            return self.__build_premium_pocket_square_sku(shopify_sku)
        else:
            raise ServiceError("Unsupported product type")

    def __get_product_type_by_sku(self, sku: str) -> ProductType:
        prefix = sku[0]

        for product_type in ProductType:
            if product_type.value == prefix:
                return product_type

        raise ServiceError(f"Unsupported SKU type: {sku}")

    def __build_jacket_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        if size_model.jacket_size not in JACKET_SIZES:
            raise ServiceError(f"Unsupported jacket size: {size_model.jacket_size}")

        if size_model.jacket_length not in JACKET_LENGTHS:
            raise ServiceError(f"Unsupported jacket length: {size_model.jacket_length}")

        return f"{shopify_sku}{size_model.jacket_size}{size_model.jacket_length}AF"

    def __build_vest_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        if size_model.vest_size not in VEST_SIZES:
            raise ServiceError(f"Unsupported vest size: {size_model.vest_size}")

        vest_size_code = VEST_SIZE_CODES.get(size_model.vest_size)

        if not vest_size_code:
            raise ServiceError(f"Unsupported vest size: {size_model.vest_size}")

        return f"{shopify_sku}{vest_size_code}{size_model.vest_length}AF"

    def __build_pants_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        if size_model.pant_size not in PANT_SIZES:
            raise ServiceError(f"Unsupported pant size: {size_model.pant_size}")

        if size_model.pant_length not in PANT_LENGTHS:
            raise ServiceError(f"Unsupported pant length: {size_model.pant_length}")

        autofill_suffix = "AF" if int(size_model.jacket_size) - int(size_model.pant_size) == 6 else ""

        return f"{shopify_sku}{size_model.pant_size}{size_model.pant_length}{autofill_suffix}"

    def __build_shirt_sku(self, shopify_sku: str, size_model: SizeModel) -> str:
        if size_model.shirt_neck_size not in SHIRT_NECK_SIZES:
            raise ServiceError(f"Unsupported shirt neck size: {size_model.shirt_neck_size}")

        if size_model.shirt_sleeve_length not in SHIRT_SLEEVE_LENGTHS:
            raise ServiceError(f"Unsupported shirt sleeve length: {size_model.shirt_sleeve_length}")

        shirt_neck_size = SHIRT_NECK_SIZES_MAP.get(size_model.shirt_neck_size)
        shirt_length_code = SHIRT_SLEEVE_LENGTHS_MAP.get(size_model.shirt_sleeve_length)

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
            pant_size = "460"
        elif 48 <= pant_size_num <= 60:
            pant_size = "600"
        else:
            raise ServiceError(f"Unsupported pant size: {size_model.pant_size}")

        return f"{shopify_sku}{pant_size}R"

    def __build_shoes_sku(self, shopify_sku: str, measurement_model: MeasurementModel) -> str:
        shoe_size = SHOES_SIZE_CODES.get(measurement_model.shoe_size)

        if not shoe_size:
            raise ServiceError(f"Unsupported shoe size: {measurement_model.shoe_size}")

        return f"{shopify_sku}{shoe_size}"

    def __build_socks_sku(self, shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"

    def __build_swatches_sku(self, shopify_sku: str) -> str:
        return shopify_sku

    def __build_premium_pocket_square_sku(self, shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"
