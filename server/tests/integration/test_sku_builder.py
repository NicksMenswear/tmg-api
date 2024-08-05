import csv
import unittest
from typing import Set

from parameterized import parameterized

from server.services.sku_builder_service import (
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

    def test_belt_ship_hero_product_availability(self):
        shopify_belts = TestSkuBuilder.read_csv_into_set("assets/shopify_belts.csv")

        for shopify_belt in shopify_belts:
            for pant_size in PANT_SIZES:
                shiphero_sku = self.sku_builder.build(
                    shopify_belt,
                    fixtures.size_model(pant_size=pant_size),
                    fixtures.measurement_model(),
                )

                if shiphero_sku in self.shiphero_skus:
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

    @parameterized.expand(
        [
            ["001A1BLK", "34", "R", "001A1BLK36R"],
            ["001A1BLK", "34", "L", "001A1BLK38L"],
            ["001A1BLK", "36", "L", "001A1BLK38L"],
            ["001A1BLK", "50", "X", "001A1BLK50L"],
            ["001A1BLK", "52", "X", "001A1BLK52L"],
            ["001A1BLK", "54", "X", "001A1BLK54L"],
            ["001A1BLK", "56", "X", "001A1BLK56L"],
            ["001A1BLK", "58", "X", "001A1BLK58L"],
            ["001A1BLK", "60", "X", "001A1BLK60L"],
            ["001A1BLK", "62", "X", "001A1BLK62L"],
            ["001A1BLK", "64", "X", "001A1BLK64L"],
            ["001A1BLK", "66", "X", "001A1BLK66L"],
            ["001A1BLK", "54", "S", "001A1BLK54R"],
            ["001A1BLK", "56", "S", "001A1BLK56R"],
            ["001A1BLK", "58", "S", "001A1BLK58R"],
            ["001A1BLK", "60", "S", "001A1BLK60R"],
            ["001A1BLK", "62", "S", "001A1BLK62R"],
            ["001A1BLK", "64", "S", "001A1BLK64R"],
            ["001A1BLK", "66", "S", "001A1BLK66R"],
        ]
    )
    def test_special_cases_correctness_for_suits(self, shopify_sku, jacket_size, jacket_length, expected_sku):
        shiphero_sku = self.sku_builder.build(
            shopify_sku,
            fixtures.size_model(jacket_size=jacket_size, jacket_length=jacket_length),
            fixtures.measurement_model(),
        )

        self.assertEqual(expected_sku, shiphero_sku)

    @parameterized.expand(
        [
            ["101A1BLK", "34", "R", "101A1BLK36RAF"],
            ["101A1BLK", "34", "L", "101A1BLK38LAF"],
            ["101A1BLK", "36", "L", "101A1BLK38LAF"],
            ["101A1BLK", "50", "X", "101A1BLK50LAF"],
            ["101A1BLK", "52", "X", "101A1BLK52LAF"],
            ["101A1BLK", "54", "X", "101A1BLK54LAF"],
            ["101A1BLK", "56", "X", "101A1BLK56LAF"],
            ["101A1BLK", "58", "X", "101A1BLK58LAF"],
            ["101A1BLK", "60", "X", "101A1BLK60LAF"],
            ["101A1BLK", "62", "X", "101A1BLK62LAF"],
            ["101A1BLK", "64", "X", "101A1BLK64LAF"],
            ["101A1BLK", "66", "X", "101A1BLK66LAF"],
            ["101A1BLK", "54", "S", "101A1BLK54RAF"],
            ["101A1BLK", "56", "S", "101A1BLK56RAF"],
            ["101A1BLK", "58", "S", "101A1BLK58RAF"],
            ["101A1BLK", "60", "S", "101A1BLK60RAF"],
            ["101A1BLK", "62", "S", "101A1BLK62RAF"],
            ["101A1BLK", "64", "S", "101A1BLK64RAF"],
            ["101A1BLK", "66", "S", "101A1BLK66RAF"],
        ]
    )
    def test_special_cases_correctness_for_jackets(self, shopify_sku, jacket_size, jacket_length, expected_sku):
        shiphero_sku = self.sku_builder.build(
            shopify_sku,
            fixtures.size_model(jacket_size=jacket_size, jacket_length=jacket_length),
            fixtures.measurement_model(),
        )

        self.assertEqual(expected_sku, shiphero_sku)

    @parameterized.expand(
        [
            ["403A2BLK", "14", "34/35", "403A2BLK1455"],
            ["403A2BLK", "15", "36/37", "403A2BLK1507"],
        ]
    )
    def test_special_cases_correctness_for_shirts(
        self, shopify_sku, shirt_neck_size, shirt_sleeve_length, expected_sku
    ):
        shiphero_sku = self.sku_builder.build(
            shopify_sku,
            fixtures.size_model(shirt_neck_size=shirt_neck_size, shirt_sleeve_length=shirt_sleeve_length),
            fixtures.measurement_model(),
        )

        self.assertEqual(expected_sku, shiphero_sku)
