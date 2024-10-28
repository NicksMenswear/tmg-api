import logging
from enum import Enum
from typing import Optional

from server.models.measurement_model import MeasurementModel
from server.models.size_model import SizeModel
from server.services import ServiceError

# jackets
JACKET_SIZES = {"34", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66"}
JACKET_LENGTHS = {"S", "R", "L", "X", "XL"}
JACKET_LENGTHS_MAP = {
    "S": "S",
    "R": "R",
    "L": "L",
    "X": "X",
    "XL": "X",
}

# vests
VEST_SIZES = {"34", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66"}
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
    "66": "06X",
}

# pants
PANT_SIZES = {"28", "30", "32", "34", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58"}
PANT_LENGTHS = {"R"}  # set of 1 for now, ¯\_(ツ)_/¯

# shirts
SHIRT_NECK_SIZES = {
    "14",
    "14.5",
    "14 1/2",
    "15",
    "15.5",
    "15 1/2",
    "16",
    "16.5",
    "16 1/2",
    "17",
    "17.5",
    "17 1/2",
    "18",
    "18.5",
    "18 1/2",
    "19",
    "19.5",
    "19 1/2",
    "20",
    "21",
    "22",
    "23",
}

SHIRT_SLEEVE_LENGTHS = {
    "32/33",
    "34/35",
    "36/37",
    "38/39",
}

SHIRT_SIZES_MAP = {
    "14::32/33": "1403",
    "14::34/35": "1405",
    "14::36/37": "1507",
    "14::38/39": "1507",
    "14.5::32/33": "1453",
    "14.5::34/35": "1455",
    "14.5::36/37": "1507",
    "14.5::38/39": "1507",
    "14 1/2::32/33": "1453",
    "14 1/2::34/35": "1455",
    "14 1/2::36/37": "1507",
    "14 1/2::38/39": "1507",
    "15::32/33": "1503",
    "15::34/35": "1505",
    "15::36/37": "1507",
    "15::38/39": "1507",
    "15.5::32/33": "1553",
    "15.5::34/35": "1555",
    "15.5::36/37": "1557",
    "15.5::38/39": "1557",
    "15 1/2::32/33": "1553",
    "15 1/2::34/35": "1555",
    "15 1/2::36/37": "1557",
    "15 1/2::38/39": "1557",
    "16::32/33": "1603",
    "16::34/35": "1605",
    "16::36/37": "1607",
    "16::38/39": "1607",
    "16.5::32/33": "1653",
    "16.5::34/35": "1655",
    "16.5::36/37": "1657",
    "16.5::38/39": "1659",
    "16 1/2::32/33": "1653",
    "16 1/2::34/35": "1655",
    "16 1/2::36/37": "1657",
    "16 1/2::38/39": "1659",
    "17::32/33": "1703",
    "17::34/35": "1705",
    "17::36/37": "1707",
    "17::38/39": "1709",
    "17.5::32/33": "1753",
    "17.5::34/35": "1755",
    "17.5::36/37": "1757",
    "17.5::38/39": "1759",
    "17 1/2::32/33": "1753",
    "17 1/2::34/35": "1755",
    "17 1/2::36/37": "1757",
    "17 1/2::38/39": "1759",
    "18::32/33": "1803",
    "18::34/35": "1805",
    "18::36/37": "1807",
    "18::38/39": "1809",
    "18.5::32/33": "1853",
    "18.5::34/35": "1855",
    "18.5::36/37": "1857",
    "18.5::38/39": "1859",
    "18 1/2::32/33": "1853",
    "18 1/2::34/35": "1855",
    "18 1/2::36/37": "1857",
    "18 1/2::38/39": "1859",
    "19::32/33": "1903",
    "19::34/35": "1905",
    "19::36/37": "1907",
    "19::38/39": "1909",
    "19.5::32/33": "1955",
    "19.5::34/35": "1955",
    "19.5::36/37": "1957",
    "19.5::38/39": "1957",
    "19 1/2::32/33": "1955",
    "19 1/2::34/35": "1955",
    "19 1/2::36/37": "1957",
    "19 1/2::38/39": "1957",
    "20::32/33": "2003",
    "20::34/35": "2005",
    "20::36/37": "2007",
    "20::38/39": "2007",
    "20.5::32/33": "2055",
    "20.5::34/35": "2055",
    "20.5::36/37": "2057",
    "20.5::38/39": "2057",
    "21::32/33": "2105",
    "21::34/35": "2105",
    "21::36/37": "2107",
    "21::38/39": "2107",
    "21.5::32/33": "2105",
    "21.5::34/35": "2105",
    "21.5::36/37": "2107",
    "21.5::38/39": "2107",
    "22::32/33": "2205",
    "22::34/35": "2205",
    "22::36/37": "2207",
    "22::38/39": "2207",
    "22.5::32/33": "2205",
    "22.5::34/35": "2205",
    "22.5::36/37": "2207",
    "22.5::38/39": "2207",
    "23::32/33": "2305",
    "23::34/35": "2305",
    "23::36/37": "2307",
    "23::38/39": "2307",
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
    GARMENT_BAG = "G"
    UNKNOWN = "UNKNOWN"


PRODUCT_TYPES_THAT_REQUIRES_MEASUREMENTS = {
    ProductType.SUIT,
    ProductType.JACKET,
    ProductType.PANTS,
    ProductType.VEST,
    ProductType.SHIRT,
    ProductType.BELT,
    ProductType.SHOES,
}

logger = logging.getLogger(__name__)


class SkuBuilder:
    def build(self, shopify_sku: str, size_model: SizeModel, measurement_model: MeasurementModel) -> Optional[str]:
        product_type = self.get_product_type_by_sku(shopify_sku)

        if size_model:
            self.__handle_special_sizes(size_model)

        if product_type == ProductType.SUIT:
            return self.__build_suit_sku(shopify_sku, size_model) if size_model else None
        elif product_type == ProductType.JACKET:
            return self.__build_jacket_sku(shopify_sku, size_model) if size_model else None
        elif product_type == ProductType.PANTS:
            return self.__build_pants_sku(shopify_sku, size_model) if size_model else None
        elif product_type == ProductType.VEST:
            return self.__build_vest_sku(shopify_sku, size_model) if size_model else None
        elif product_type == ProductType.SHIRT:
            return self.__build_shirt_sku(shopify_sku, size_model) if size_model else None
        elif product_type == ProductType.NECK_TIE:
            return self.__build_neck_tie_sku(shopify_sku)
        elif product_type == ProductType.BOW_TIE:
            return self.__build_bow_tie_sku(shopify_sku)
        elif product_type == ProductType.BELT:
            return self.__build_belt_sku(shopify_sku, size_model) if size_model else None
        elif product_type == ProductType.SHOES:
            return self.__build_shoes_sku(shopify_sku, measurement_model) if measurement_model else None
        elif product_type == ProductType.SOCKS:
            return self.__build_socks_sku(shopify_sku)
        elif product_type == ProductType.SOCKS:
            return self.__build_socks_sku(shopify_sku)
        elif product_type == ProductType.SWATCHES:
            return self.__build_swatches_sku(shopify_sku)
        elif product_type == ProductType.PREMIUM_POCKET_SQUARE:
            return self.__build_premium_pocket_square_sku(shopify_sku)
        elif product_type == ProductType.GARMENT_BAG:
            return shopify_sku
        else:
            return None

    def does_product_requires_measurements(self, sku) -> bool:
        product_type = self.get_product_type_by_sku(sku)
        return product_type in PRODUCT_TYPES_THAT_REQUIRES_MEASUREMENTS

    @staticmethod
    def get_product_type_by_sku(sku: str) -> ProductType:
        prefix = sku[0] if sku else ""

        for product_type in ProductType:
            if product_type.value == prefix:
                return product_type

        return ProductType.UNKNOWN

    @staticmethod
    def __validate_jacket_sizes(size_model: SizeModel):
        if size_model.jacket_size not in JACKET_SIZES:
            raise ServiceError(f"Unsupported jacket size: {size_model.jacket_size}")

        if size_model.jacket_length not in JACKET_LENGTHS:
            raise ServiceError(f"Unsupported jacket length: {size_model.jacket_length}")

    @staticmethod
    def __validate_shirt_sizes(size_model: SizeModel):
        if size_model.shirt_neck_size not in SHIRT_NECK_SIZES:
            raise ServiceError(f"Unsupported shirt neck size: {size_model.shirt_neck_size}")

        if size_model.shirt_sleeve_length not in SHIRT_SLEEVE_LENGTHS:
            raise ServiceError(f"Unsupported shirt sleeve length: {size_model.shirt_sleeve_length}")

    @staticmethod
    def __validate_pant_sizes(size_model: SizeModel):
        if size_model.pant_size not in PANT_SIZES:
            raise ServiceError(f"Unsupported pant size: {size_model.pant_size}")

        if size_model.pant_length not in PANT_LENGTHS:
            raise ServiceError(f"Unsupported pant length: {size_model.pant_length}")

    @staticmethod
    def __validate_vest_sizes(size_model: SizeModel):
        if size_model.vest_size not in VEST_SIZES:
            raise ServiceError(f"Unsupported vest size: {size_model.vest_size}")

    def __handle_special_sizes(self, size_model: SizeModel):
        self.__validate_jacket_sizes(size_model)
        self.__validate_vest_sizes(size_model)

        # special cases for jackets, suit and vest
        if int(size_model.jacket_size) < 36 and size_model.jacket_length == "R":
            size_model.jacket_size = "36"
            size_model.jacket_length = "R"
            size_model.vest_size = size_model.jacket_size
        elif int(size_model.jacket_size) < 38 and size_model.jacket_length == "L":
            size_model.jacket_size = "38"
            size_model.jacket_length = "L"
            size_model.vest_size = size_model.jacket_size
        elif int(size_model.jacket_size) >= 50 and (
            size_model.jacket_length == "X" or size_model.jacket_length == "XL"
        ):
            size_model.jacket_length = "L"
        elif int(size_model.jacket_size) >= 54 and size_model.jacket_length == "S":
            size_model.jacket_length = "R"

        self.__validate_shirt_sizes(size_model)

        # special cases for shirts
        if size_model.shirt_neck_size == "14" and size_model.shirt_sleeve_length == "34/35":
            size_model.shirt_neck_size = "14.5"
        elif size_model.shirt_neck_size in ["14", "14.5", "14 1/2", "15"] and size_model.shirt_sleeve_length == "36/37":
            size_model.shirt_neck_size = "15.5"

    def __build_suit_sku(self, shopify_sku: str, size_model: SizeModel) -> Optional[str]:
        self.__validate_jacket_sizes(size_model)

        jacket_length_code = JACKET_LENGTHS_MAP.get(size_model.jacket_length)

        return f"{shopify_sku}{size_model.jacket_size}{jacket_length_code}"

    def __build_jacket_sku(self, shopify_sku: str, size_model: SizeModel) -> Optional[str]:
        self.__validate_jacket_sizes(size_model)

        jacket_length_code = JACKET_LENGTHS_MAP.get(size_model.jacket_length)

        return f"{shopify_sku}{size_model.jacket_size}{jacket_length_code}AF"

    def __build_vest_sku(self, shopify_sku: str, size_model: SizeModel) -> Optional[str]:
        self.__validate_vest_sizes(size_model)

        vest_size_code = VEST_SIZE_CODES.get(size_model.vest_size)

        return f"{shopify_sku}{vest_size_code}{size_model.vest_length}AF"

    def __build_pants_sku(self, shopify_sku: str, size_model: SizeModel) -> Optional[str]:
        self.__validate_pant_sizes(size_model)

        autofill_suffix = "AF" if int(size_model.jacket_size) - int(size_model.pant_size) == 6 else ""

        return f"{shopify_sku}{size_model.pant_size}{size_model.pant_length}{autofill_suffix}"

    def __build_shirt_sku(self, shopify_sku: str, size_model: SizeModel) -> Optional[str]:
        self.__validate_shirt_sizes(size_model)

        shirt_size_key = f"{size_model.shirt_neck_size}::{size_model.shirt_sleeve_length}"
        shirt_size_code = SHIRT_SIZES_MAP.get(shirt_size_key)

        return f"{shopify_sku}{shirt_size_code}"

    @staticmethod
    def __build_neck_tie_sku(shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"

    @staticmethod
    def __build_bow_tie_sku(shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"

    def __build_belt_sku(self, shopify_sku: str, size_model: SizeModel) -> Optional[str]:
        self.__validate_pant_sizes(size_model)

        pant_size_num = int(size_model.pant_size)

        if 28 <= pant_size_num <= 46:
            pant_size = "460"
        else:
            pant_size = "600"

        return f"{shopify_sku}{pant_size}R"

    @staticmethod
    def __build_shoes_sku(shopify_sku: str, measurement_model: MeasurementModel) -> Optional[str]:
        shoe_size = SHOES_SIZE_CODES.get(measurement_model.shoe_size)

        if not shoe_size:
            raise ServiceError(f"Unsupported shoe size: {measurement_model.shoe_size}")

        return f"{shopify_sku}{shoe_size}"

    @staticmethod
    def __build_socks_sku(shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"

    @staticmethod
    def __build_swatches_sku(shopify_sku: str) -> str:
        return shopify_sku

    @staticmethod
    def __build_premium_pocket_square_sku(shopify_sku: str) -> str:
        return f"{shopify_sku}OSR"
