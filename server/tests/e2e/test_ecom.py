import random
import time

import pytest
from playwright.sync_api import Page

from server.tests.e2e import e2e_allowed_in, e2e_error_handling, TEST_USER_EMAIL, TEST_USER_PASSWORD, STORE_URL
from server.tests.e2e.utils import actions, verify

SHOES_SIZES = ["7", "7.5", "8", "8.5", "9", "9 Wide"]  # this is a subset of sizes
BELT_SIZES = ["28 - 46", "48+"]


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_9
def test_buy_sized_shoes_and_tie(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    shoes_size = random.choice(SHOES_SIZES)

    page.goto(f"{STORE_URL}/products/black-dress-shoes")
    page.locator(f"div.swatch__option[data-variant-option-value-wrapper=''] input[aria-label='{shoes_size}']").locator(
        ".."
    ).click()

    actions.click_add_to_cart_on_product_page(page)

    time.sleep(3)

    page.goto(f"{STORE_URL}/products/apple-red-bow-tie")
    actions.click_add_to_cart_on_product_page(page)

    actions.click_on_cart_checkout_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, "Apple Red Bow Tie", "40", True)
    verify.shopify_checkout_has_item_with_name_and_price(page, "Black Dress Shoes", "115", False)
    actions.shopify_checkout_continue_to_shipping(page, "ASDf", "ASDF")
    verify.shopify_checkout_shipping_method_is(page, "UPS Ground", "$10.00")


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_7
def test_buy_black_belt(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    belt_size = random.choice(BELT_SIZES)

    page.goto(f"{STORE_URL}/products/black-adjustable-belt")
    page.locator(f"div.swatch__option[data-variant-option-value-wrapper=''] input[aria-label='{belt_size}']").locator(
        ".."
    ).click()

    actions.click_add_to_cart_on_product_page(page)

    time.sleep(3)

    page.goto(f"{STORE_URL}/products/apple-red-bow-tie")
    actions.click_add_to_cart_on_product_page(page)

    actions.click_on_cart_checkout_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, "Apple Red Bow Tie", "40", True)
    verify.shopify_checkout_has_item_with_name_and_price(page, "Black Adjustable Belt", "30", False)
    actions.shopify_checkout_continue_to_shipping(page, "ASDf", "ASDF")
    verify.shopify_checkout_shipping_method_is(page, "UPS Ground", "$10.00")
