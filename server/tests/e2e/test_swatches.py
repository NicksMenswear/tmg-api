import pytest
from playwright.sync_api import Page

from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, e2e_error_handling, e2e_allowed_in
from server.tests.e2e.utils import actions, verify


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_order_swatches(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    actions.add_swatch_to_cart(page, 0)
    actions.continue_shopping(page)
    actions.add_swatch_to_cart(page, 1)
    actions.verify_cart_message(page, "You have used 2 of 5 free swatches.")

    actions.click_on_cart_checkout_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, f"Black Suit And Tuxedo Swatch", "FREE", True)
    verify.shopify_checkout_has_item_with_name_and_price(page, f"Charcoal Grey Suit Swatch", "FREE", False)
