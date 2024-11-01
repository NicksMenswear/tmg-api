import time

import pytest
from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, e2e_error_handling, e2e_allowed_in, STORE_URL
from server.tests.e2e.utils import actions, verify, api


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_4
def test_shipping_customer_buys_a_suit_so_free_shipping(page: Page):
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    owner_user = api.get_user_by_email(TEST_USER_EMAIL)
    user_id = owner_user.get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    actions.add_look_to_cart(page, data_look_id)

    actions.populate_get_started_dialog(page)
    time.sleep(3)

    page.goto(f"{STORE_URL}/pages/looks")

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)
    actions.add_look_to_cart(page, data_look_id)
    verify.shopify_checkout_has_item_with_name_and_price(page, look_name, f"${str(price)}")
    actions.shopify_checkout_continue_to_shipping(page, owner_user.get("first_name"), owner_user.get("last_name"))
    verify.shopify_checkout_shipping_method_is(page, "UPS Ground", "FREE")


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_free_shipping_for_swatches_forever(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    swatch_name = actions.add_swatch_to_cart(page, 0)
    actions.continue_shopping(page)
    actions.click_on_cart_checkout_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, swatch_name, "FREE", True)
    actions.shopify_checkout_continue_to_shipping(page, "ASDf", "ASDF")
    verify.shopify_checkout_shipping_method_is(page, "UPS Ground", "FREE")


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_6
def test_standard_10usd_shipping_for_items_under_210(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    page.goto(f"{STORE_URL}/products/apple-red-bow-tie")

    actions.click_add_to_cart_on_product_page(page)
    actions.click_on_cart_checkout_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, "Apple Red Bow Tie", "40", True)
    actions.shopify_checkout_continue_to_shipping(page, "ASDf", "ASDF")
    verify.shopify_checkout_shipping_method_is(page, "UPS Ground", "$10.00")


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_7
def test_free_shipping_for_multiple_cheap_items_over_210_in_total(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    page.goto(f"{STORE_URL}/products/apple-red-bow-tie")

    actions.click_add_to_cart_on_product_page(page)
    actions.press_plus_button_to_increase_quantity_in_cart(page)
    actions.click_on_cart_checkout_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, "Apple Red Bow Tie", "240", True)
    actions.shopify_checkout_continue_to_shipping(page, "ASDf", "ASDF")
    verify.shopify_checkout_shipping_method_is(page, "UPS Ground", "FREE")
