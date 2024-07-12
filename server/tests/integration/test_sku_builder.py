import csv
import unittest
from typing import Set

from server.services.sku_builder import (
    SkuBuilder,
    JACKET_LENGTHS,
    JACKET_SIZES,
    VEST_SIZES,
    VEST_LENGTHS,
    PANT_SIZES,
    PANT_LENGTHS,
    SHIRT_NECK_SIZES,
    SHIRT_SLEEVE_LENGTHS,
    SHOES_SIZE_CODES,
)
from server.tests.integration import fixtures


class TestSkuBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shiphero_skus = TestSkuBuilder.read_csv_into_set("assets/ship_hero_skus.csv")

    def setUp(self):
        self.sku_builder = SkuBuilder()

    @staticmethod
    def read_csv_into_set(file: str) -> Set[str]:
        result = set()

        with open(file, newline="") as csvfile:
            csvreader = csv.reader(csvfile)

            for row in csvreader:
                if row[0]:
                    result.add(row[0])

        return result

    def test_jacket_ship_hero_product_availability(self):
        shopify_jackets = TestSkuBuilder.read_csv_into_set("assets/shopify_jackets.csv")
        shiphero_skus_jacket_excludes = TestSkuBuilder.read_csv_into_set(
            "assets/ship_hero_skus_jacket_known_excludes.csv"
        )

        for shopify_jacket in shopify_jackets:
            for jacket_size in JACKET_SIZES:
                for jacket_length in JACKET_LENGTHS:
                    shiphero_sku = self.sku_builder.build(
                        shopify_jacket,
                        fixtures.size_model(jacket_size=jacket_size, jacket_length=jacket_length),
                        fixtures.measurement_model(),
                    )

                    if shiphero_sku in self.shiphero_skus:
                        continue
                    elif shiphero_sku in shiphero_skus_jacket_excludes:
                        continue
                    else:
                        raise Exception(f"SKU not found: {shiphero_sku}")

    def test_vest_ship_hero_product_availability(self):
        shopify_vests = TestSkuBuilder.read_csv_into_set("assets/shopify_vests.csv")

        for shopify_vest in shopify_vests:
            for vest_size in VEST_SIZES:
                for vest_length in VEST_LENGTHS:
                    shiphero_sku = self.sku_builder.build(
                        shopify_vest,
                        fixtures.size_model(vest_size=vest_size, vest_length=vest_length),
                        fixtures.measurement_model(),
                    )

                    if shiphero_sku in self.shiphero_skus:
                        continue
                    else:
                        raise Exception(f"SKU not found: {shiphero_sku}")

    def test_pants_ship_hero_product_availability(self):
        shopify_pants = TestSkuBuilder.read_csv_into_set("assets/shopify_pants.csv")
        shiphero_skus_pants_excludes = TestSkuBuilder.read_csv_into_set(
            "assets/ship_hero_skus_pants_known_excludes.csv"
        )

        for shopify_pant in shopify_pants:
            for pant_size in PANT_SIZES:
                for pant_length in PANT_LENGTHS:
                    shiphero_sku = self.sku_builder.build(
                        shopify_pant,
                        fixtures.size_model(pant_size=pant_size, pant_length=pant_length),
                        fixtures.measurement_model(),
                    )

                    if shiphero_sku in self.shiphero_skus:
                        continue
                    elif shiphero_sku in shiphero_skus_pants_excludes:
                        continue
                    else:
                        raise Exception(f"SKU not found: {shiphero_sku}")

    def test_shirts_ship_hero_product_availability(self):
        shopify_shirts = TestSkuBuilder.read_csv_into_set("assets/shopify_shirts.csv")
        shiphero_skus_shirts_excludes = TestSkuBuilder.read_csv_into_set(
            "assets/ship_hero_skus_shirts_known_excludes.csv"
        )

        for shopify_shirt in shopify_shirts:
            for shirt_neck_size in SHIRT_NECK_SIZES:
                for shirt_sleeve_length in SHIRT_SLEEVE_LENGTHS:
                    shiphero_sku = self.sku_builder.build(
                        shopify_shirt,
                        fixtures.size_model(shirt_neck_size=shirt_neck_size, shirt_sleeve_length=shirt_sleeve_length),
                        fixtures.measurement_model(),
                    )

                    if shiphero_sku in self.shiphero_skus:
                        continue
                    elif shiphero_sku in shiphero_skus_shirts_excludes:
                        continue
                    else:
                        raise Exception(f"SKU not found: {shiphero_sku}")

    def test_neck_tie_ship_hero_product_availability(self):
        shopify_neck_ties = TestSkuBuilder.read_csv_into_set("assets/shopify_neck_ties.csv")

        for shopify_neck_tie in shopify_neck_ties:
            shiphero_sku = self.sku_builder.build(
                shopify_neck_tie,
                fixtures.size_model(),
                fixtures.measurement_model(),
            )

            if shiphero_sku in self.shiphero_skus:
                continue
            else:
                raise Exception(f"SKU not found: {shiphero_sku}")

    def test_bow_tie_ship_hero_product_availability(self):
        shopify_bow_ties = TestSkuBuilder.read_csv_into_set("assets/shopify_bow_ties.csv")

        for shopify_bow_tie in shopify_bow_ties:
            shiphero_sku = self.sku_builder.build(
                shopify_bow_tie,
                fixtures.size_model(),
                fixtures.measurement_model(),
            )

            if shiphero_sku in self.shiphero_skus:
                continue
            else:
                raise Exception(f"SKU not found: {shiphero_sku}")

    def test_shoes_ship_hero_product_availability(self):
        shopify_shoes = TestSkuBuilder.read_csv_into_set("assets/shopify_shoes.csv")
        shiphero_skus_shoes_excludes = TestSkuBuilder.read_csv_into_set(
            "assets/ship_hero_skus_shoes_known_excludes.csv"
        )

        for shopify_shoe in shopify_shoes:
            for shoe_size in SHOES_SIZE_CODES.keys():
                shiphero_sku = self.sku_builder.build(
                    shopify_shoe,
                    fixtures.size_model(),
                    fixtures.measurement_model(shoe_size=shoe_size),
                )

                if shiphero_sku in self.shiphero_skus:
                    continue
                elif shiphero_sku in shiphero_skus_shoes_excludes:
                    continue
                else:
                    raise Exception(f"SKU not found: {shiphero_sku}")

    def test_socks_ship_hero_product_availability(self):
        shopify_socks = TestSkuBuilder.read_csv_into_set("assets/shopify_socks.csv")

        for shopify_sock in shopify_socks:
            shiphero_sku = self.sku_builder.build(
                shopify_sock,
                fixtures.size_model(),
                fixtures.measurement_model(),
            )

            if shiphero_sku in self.shiphero_skus:
                continue
            else:
                raise Exception(f"SKU not found: {shiphero_sku}")

    def test_swatches_ship_hero_product_availability(self):
        shopify_swatches = TestSkuBuilder.read_csv_into_set("assets/shopify_swatches.csv")

        for shopify_swatch in shopify_swatches:
            shiphero_sku = self.sku_builder.build(
                shopify_swatch,
                fixtures.size_model(),
                fixtures.measurement_model(),
            )

            if shiphero_sku in self.shiphero_skus:
                continue
            else:
                raise Exception(f"SKU not found: {shiphero_sku}")

    def test_shopify_premium_pocket_square_ship_hero_product_availability(self):
        shopify_premium_pocket_squares = TestSkuBuilder.read_csv_into_set("assets/shopify_premium_pocket_squares.csv")

        for shopify_premium_pocket_square in shopify_premium_pocket_squares:
            shiphero_sku = self.sku_builder.build(
                shopify_premium_pocket_square,
                fixtures.size_model(),
                fixtures.measurement_model(),
            )

            if shiphero_sku in self.shiphero_skus:
                continue
            else:
                raise Exception(f"SKU not found: {shiphero_sku}")
